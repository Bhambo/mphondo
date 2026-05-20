const { getDefaultConfig } = require("expo/metro-config");
const { withNativeWind } = require("nativewind/metro");

const config = getDefaultConfig(__dirname);

// Prevent Metro from picking up ESM entry points (via package.json "exports" field).
// ESM builds often contain `import.meta` which the Metro web bundle can't handle
// because the output script tag is not type="module".
config.resolver.unstable_enablePackageExports = false;

module.exports = withNativeWind(config, { input: "./global.css" });
