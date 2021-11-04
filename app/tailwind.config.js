module.exports = {
    purge: {
        enabled: true,
        content: ['./templates/**/*.html',
            './**/js/*.js']
    },
    darkMode: 'class', // or 'media' or 'class'
    theme: {
        extend: {},
    },
    variants: {
        extend: {},
    },
    plugins: [
        require('@tailwindcss/forms'),
    ],
}
