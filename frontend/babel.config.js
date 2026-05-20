module.exports = function (api) {
  api.cache(true);
  return {
    presets: [
      require.resolve("babel-preset-expo"),
      require.resolve("nativewind/babel"),
    ],
    plugins: [
      require.resolve("babel-plugin-transform-import-meta"),
      require.resolve("react-native-reanimated/plugin"),
    ],
  };
};
