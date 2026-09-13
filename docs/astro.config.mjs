// @ts-check
import { defineConfig } from "astro/config";
import { unified } from "@astrojs/markdown-remark";
import starlight from "@astrojs/starlight";
import tailwindcss from "@tailwindcss/vite";
import mdx from "@astrojs/mdx";
import react from "@astrojs/react";
import remarkMath from "remark-math";
import rehypeMathjax from "rehype-mathjax";

// https://astro.build/config
export default defineConfig({
  site: "https://tum-esm.github.io",
  base: "/em27-retrieval-pipeline",
  integrations: [
    starlight({
      title: "EM27 Retrieval Pipeline",
      logo: {
        light: "./src/assets/logo.svg",
        dark: "./src/assets/logo-dark.svg",
      },
      social: [
        {
          icon: "github",
          label: "GitHub",
          href: "https://github.com/tum-esm/em27-retrieval-pipeline",
        },
      ],
      editLink: {
        baseUrl:
          "https://github.com/tum-esm/em27-retrieval-pipeline/edit/main/",
      },
      sidebar: [
        {
          label: "Index",
          link: "/",
        },
        {
          label: "Guides",
          collapsed: false,
          items: [
            {
              label: "Quick Start",
              link: "/guides/quick-start",
            },
            {
              label: "Configuration",
              link: "/guides/configuration",
            },
            {
              label: "EM27 Metadata",
              link: "/guides/em27-metadata",
            },
            {
              label: "Data Directories",
              link: "/guides/data-directories",
            },
            {
              label: "Full Usage Guide",
              link: "/guides/full-usage-guide",
            },
            {
              label: "Configuration Migration",
              link: "/guides/configuration-migration",
            },
            {
              label: "FAQ",
              link: "/guides/faq",
            },
          ],
        },
        {
          label: "Developer Guides",
          collapsed: true,
          items: [
            {
              label: "Contributing",
              link: "/other/contributing",
            },
            {
              label: "Internal Data Directories",
              link: "/other/internal-data-directories",
            },
            {
              label: "Tests",
              link: "/other/tests",
            },
            {
              label: "EM27 Metadata Tests",
              link: "/other/em27-metadata-tests",
            },
          ],
        },
        {
          label: "API Reference",
          collapsed: false,
          items: [
            {
              label: "Configuration",
              link: "/reference/config",
            },
            {
              label: "GEOMS Metadata",
              link: "/reference/geoms_metadata",
            },
            {
              label: "Command Line Interface",
              link: "/reference/cli",
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
        "@fontsource/rubik/300.css",
        "@fontsource/rubik/300-italic.css",
        "@fontsource/rubik/400.css",
        "@fontsource/rubik/400-italic.css",
        "@fontsource/rubik/500.css",
        "@fontsource/rubik/500-italic.css",
        "@fontsource/rubik/600.css",
        "@fontsource/rubik/600-italic.css",
        "@fontsource/rubik/700.css",
        "@fontsource/rubik/700-italic.css",
      ],
    }),
    react(),
    mdx(),
  ],
  markdown: {
    processor: unified({
      remarkPlugins: [remarkMath],
      rehypePlugins: [rehypeMathjax],
    }),
  },
  vite: {
    plugins: [tailwindcss()],
  },
});
