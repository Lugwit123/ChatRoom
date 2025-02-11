module.exports = {
    parser: '@typescript-eslint/parser',
    extends: [
        'plugin:react/recommended',
        'plugin:@typescript-eslint/recommended',

    ],
    plugins: ['react', '@typescript-eslint',],
    env: {
        browser: true,
        es6: true,
        node: true,
    },
    settings: {
        react: {
            version: 'detect',
        },
    },
    rules: {
        'prettier/prettier': 'error',
        '@typescript-eslint/no-explicit-any': 'error',
        // 其他规则
    },
};
