#version 330

in vec2 fragTexCoord;
in vec4 fragColor;

uniform sampler2D texture0;
uniform vec2 resolution;
uniform float pixelSize;
uniform float underwater;
uniform float depthVision;
uniform sampler2D depthTexture;
uniform float nearPlane;
uniform float farPlane;
uniform float fogDensity;
uniform vec3 fogColor;

out vec4 finalColor;

void main() {
    vec2 grid = resolution / pixelSize;
    vec2 uv = (floor(fragTexCoord * grid) + 0.5) / grid;

    vec4 color = texture(texture0, uv) * fragColor;
    color.rgb = mix(color.rgb, vec3(0.05, 0.35, 0.75), underwater * 0.5);

    float depth = texture(depthTexture, uv).r;
    float linearDepth = (2.0 * nearPlane * farPlane) /
        (farPlane + nearPlane - (2.0 * depth - 1.0) * (farPlane - nearPlane));
    float depthView = 1.0 - log(linearDepth / nearPlane) / log(farPlane / nearPlane);




    // depth vision
    color.rgb = mix(color.rgb, vec3(clamp(depthView, 0.0, 1.0)), depthVision);


    // fog
    float fogDensityAtPoint = 1.0 - clamp((depthView * depthView * fogDensity), 0.0, 1.0);
    color.rgb = mix(color.rgb, fogColor, fogDensityAtPoint * (1.0 - depthVision));



    finalColor = color;
}