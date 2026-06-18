const path = require("node:path");

const repoRoot = path.resolve(__dirname, "../..");
const packageResources = path.join(repoRoot, "packaging", "dist");

module.exports = {
  packagerConfig: {
    name: "TraceSeal",
    executableName: "TraceSeal",
    asar: true,
    extraResource: [
      path.join(packageResources, "renderer"),
      path.join(packageResources, "traceseal-core"),
    ],
    ignore: [
      /^\/node_modules\/\.cache/,
      /^\/dist\/tests/,
      /^\/tests/,
      /^\/out/,
    ],
  },
  rebuildConfig: {},
  makers: [
    {
      name: "@electron-forge/maker-squirrel",
      config: {
        name: "traceseal",
        setupExe: "TraceSeal-Setup.exe",
      },
    },
    {
      name: "@electron-forge/maker-zip",
      platforms: ["win32"],
    },
  ],
};
