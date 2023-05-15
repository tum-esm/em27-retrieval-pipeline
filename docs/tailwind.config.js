/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        './pages/**/*.{js,ts,jsx,tsx,mdx}',
        './components/**/*.{js,ts,jsx,tsx}',
        './theme.config.jsx',
    ],
    theme: {
        extend: {
            fontFamily: {
                serif: ['var(--next-font-google-crimson-pro)', 'serif'],
            },
        },
    },
    plugins: [],
    darkMode: 'class',
};
