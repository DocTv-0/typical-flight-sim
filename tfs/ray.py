from raylib import *
from pyray import *

WATER_LEVEL = 250
WIDTH, HEIGHT = 1000, 750
NEAR_PLANE, FAR_PLANE = 0.01, 1000.0


init_window(WIDTH, HEIGHT, "test")
rlSetClipPlanes(NEAR_PLANE, FAR_PLANE)
camera = Camera3D()
camera.position = Vector3(0.0, 3.0, 5.0)
camera.up = Vector3(0.0, 1.0, 0.0)
camera.target = Vector3()
camera.fovy = 45.0
camera.projection = CAMERA_PERSPECTIVE

water_surface_y = ((WATER_LEVEL / 25.5) + 0.01) / 2

target = RenderTexture()
target.id = rlLoadFramebuffer()
target.texture = Texture()
target.texture.id = rlLoadTexture(
    ffi.NULL,
    WIDTH,
    HEIGHT,
    RL_PIXELFORMAT_UNCOMPRESSED_R8G8B8A8,
    1,
)
target.texture.width = WIDTH
target.texture.height = HEIGHT
target.texture.mipmaps = 1
target.texture.format = RL_PIXELFORMAT_UNCOMPRESSED_R8G8B8A8

target.depth = Texture()
target.depth.id = rlLoadTextureDepth(WIDTH, HEIGHT, False)
target.depth.width = WIDTH
target.depth.height = HEIGHT
target.depth.mipmaps = 1

rlEnableFramebuffer(target.id)
rlFramebufferAttach(
    target.id,
    target.texture.id,
    RL_ATTACHMENT_COLOR_CHANNEL0,
    RL_ATTACHMENT_TEXTURE2D,
    0,
)
rlFramebufferAttach(
    target.id,
    target.depth.id,
    RL_ATTACHMENT_DEPTH,
    RL_ATTACHMENT_TEXTURE2D,
    0,
)
if not rlFramebufferComplete(target.id):
    raise RuntimeError("Could not create a framebuffer with a sampleable depth texture")
rlDisableFramebuffer()

shader = load_shader(ffi.NULL, "shader.fs")
resolution_loc = get_shader_location(shader, "resolution")
pixel_size_loc = get_shader_location(shader, "pixelSize")
underwater_loc = get_shader_location(shader, "underwater")
depth_vision_loc = get_shader_location(shader, "depthVision")
depth_texture_loc = get_shader_location(shader, "depthTexture")
near_plane_loc = get_shader_location(shader, "nearPlane")
far_plane_loc = get_shader_location(shader, "farPlane")
fog_density_loc = get_shader_location(shader, "fogDensity")
fog_color_loc = get_shader_location(shader, "fogColor")


set_shader_value(shader, resolution_loc, ffi.new("struct Vector2 *", Vector2(WIDTH, HEIGHT)), SHADER_UNIFORM_VEC2)
set_shader_value(shader, pixel_size_loc, ffi.new("float *", 3.0), SHADER_UNIFORM_FLOAT)
set_shader_value(shader, near_plane_loc, ffi.new("float *", NEAR_PLANE), SHADER_UNIFORM_FLOAT)
set_shader_value(shader, far_plane_loc, ffi.new("float *", FAR_PLANE), SHADER_UNIFORM_FLOAT)
set_shader_value(shader, fog_color_loc, ffi.new("struct Vector3 *", Vector3(0.55, 0.72, 0.82)), SHADER_UNIFORM_VEC3)
set_shader_value(shader, depth_texture_loc, ffi.new("int *", 1), SHADER_UNIFORM_INT)

# ground

heightmap = load_image("heightmap.png")
mesh = gen_mesh_heightmap(heightmap, Vector3(100, 10, 100))
texture = load_texture("heightmap.png")
model = load_model_from_mesh(mesh)
set_material_texture(model.materials[0], MATERIAL_MAP_ALBEDO, texture)

class Plane:
    def __init__(self, x, y, z, model):
        self.x = x
        self.y = y
        self.z = z
        self.model = model

    def draw(self):
        draw_model(
            self.model,
            (self.x, self.y, self.z),
            0.01,
            WHITE
        )

    def unload(self):
        unload_model(self.model)
        del self

f35 = Plane(
    0, 5, 0,
    load_model("f-35.glb")
)

disable_cursor()

depth_vision = 0.0

while not window_should_close():
    if is_key_pressed(KEY_R):
        depth_vision = 1 - depth_vision
    begin_drawing()

    begin_texture_mode(target)
    clear_background(BLUE)
    begin_mode_3d(camera)
    update_camera(camera, CAMERA_FREE)
    draw_model(model, Vector3(-50, 0, -50), 1.0, WHITE)
    f35.draw()
    draw_cube(Vector3(), 100, (WATER_LEVEL / 25.5) + 0.01, 100, (0, 100, 255, 75))
    end_mode_3d()
    end_texture_mode()

    underwater = 1.0 if camera.position.y < water_surface_y else 0.0
    set_shader_value(
        shader,
        underwater_loc,
        ffi.new("float *", underwater),
        SHADER_UNIFORM_FLOAT
    )
    set_shader_value(
        shader,
        underwater_loc,
        ffi.new("float *", underwater),
        SHADER_UNIFORM_FLOAT
    )
    set_shader_value(
        shader,
        depth_vision_loc,
        ffi.new("float *", depth_vision),
        SHADER_UNIFORM_FLOAT
    )
    fog_density = 10.0 if underwater else 5.0
    set_shader_value(
        shader,
        fog_density_loc,
        ffi.new("float *", fog_density),
        SHADER_UNIFORM_FLOAT
    )

    clear_background(BLACK)
    rlActiveTextureSlot(1)
    rlEnableTexture(target.depth.id)
    rlActiveTextureSlot(0)
    begin_shader_mode(shader)
    draw_texture_rec(
        target.texture,
        Rectangle(0, 0, target.texture.width, -target.texture.height),
        Vector2(0, 0),
        WHITE,
    )
    end_shader_mode()

    end_drawing()

unload_model(model)
unload_image(heightmap)
f35.unload()
rlUnloadFramebuffer(target.id)
rlUnloadTexture(target.texture.id)
rlUnloadTexture(target.depth.id)
unload_shader(shader)
close_window()