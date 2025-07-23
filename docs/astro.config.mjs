// @ts-check
import { defineConfig } from "astro/config";
import starlight from "@astrojs/starlight";
import tailwindcss from '@tailwindcss/vite';
import mdx from "@astrojs/mdx";
import react from "@astrojs/react";
import remarkMath from "remark-math";
import rehypeMathjax from "rehype-mathjax";

// https://astro.build/config
export default defineConfig({
  integrations: [
    starlight({
      title: "🌋 EM27 Retrieval Pipeline",
      social: {
        github: "https://github.com/tum-esm/em27-retrieval-pipeline",
      },
      editLink: {
        baseUrl: "https://github.com/tum-esm/em27-retrieval-pipeline/edit/main/",
      },
      sidebar: [
        {
          label: "Index",
          link: "/",
        },
        {
          label: "📚 Guides",
          items: [
            {
              label: "Configuration",
              link: "/guides/configuration",
            },
            {
              label: "Directories",
              link: "/guides/directories",
            },
            {
              label: "Metadata",
              link: "/guides/metadata",
            },
            {
              label: "Usage",
              link: "/guides/usage",
            },
            {
              label: "Test Suite",
              link: "/guides/tests",
            },
            {
              label: "Miscellaneous",
              link: "/guides/miscellaneous",
            },
          ],
        },
        {
          label: "⚙ API Reference",
          items: [
            {
              label: "Metadata",
              link: "/api-reference/metadata",
            },
            {
              label: "Configuration",
              link: "/api-reference/configuration",
            },
            {
              label: "GEOMS Configuration",
              link: "/api-reference/geoms-configuration",
            },
            {
              label: "Command Line Interface",
              link: "/api-reference/cli",
            },
          ],
        },
      ],
      customCss: [
        "./src/styles/global.css",
        "@fontsource/inter/300.css",
        "@fontsource/inter/300-italic.css",
        "@fontsource/inter/400.css",
        "@fontsource/inter/400-italic.css",
        "@fontsource/inter/500.css",
        "@fontsource/inter/500-italic.css",
        "@fontsource/inter/600.css",
        "@fontsource/inter/600-italic.css",
        "@fontsource/inter/700.css",
        "@fontsource/inter/700-italic.css",
      ],
    }),
    react(),
    mdx(),
  ],
  markdown: {
    remarkPlugins: [remarkMath],
    rehypePlugins: [rehypeMathjax],
  },
  vite: {
		plugins: [tailwindcss()],
	},
});
