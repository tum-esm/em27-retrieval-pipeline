export default {
  logo: (
    <div className="flex flex-row items-center justify-center w-[calc(100%+1.5rem)] -ml-6 gap-x-3 sm:gap-x-4">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 5334 2792"
        className="h-[var(--nextra-navbar-height)] px-4 py-[1.375rem] sm:px-[1.375rem] bg-slate-900 text-slate-50 border-r border-slate-300 dark:border-slate-700 dark:bg-transparent flex-shrink-0"
      >
        <path
          d="M4266.67,2791.67l-0,-2258.33l533.333,0l0,2258.33l533.333,-0l0,-2791.67l-2666.67,0l-0,2258.33l-533.334,0l0,-2258.33l-2133.33,0l0,533.333l533.333,0l0,2258.33l533.334,-0l-0,-2258.33l533.333,0l0,2258.33l1600,-0l0,-2258.33l533.333,0l0,2258.33l533.334,-0Z"
          className="fill-current"
        />
      </svg>
      <div className="flex-shrink-0 text-base md:text-xl whitespace-nowrap font-regular">
        <span className="font-semibold">EM27 Retrieval Pipeline</span>
        <span className="hidden lg:inline">
          {" "}
          | Professorship of Environmental Sensing and Modeling
        </span>
      </div>
    </div>
  ),
  project: {
    link: "https://github.com/tum-esm/automated-retrieval-pipeline",
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        className="icon icon-tabler icon-tabler-brand-github-filled"
        width="20"
        height="20"
        viewBox="0 0 24 24"
        strokeWidth="2"
        stroke="currentColor"
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
        <path
          d="M5.315 2.1c.791 -.113 1.9 .145 3.333 .966l.272 .161l.16 .1l.397 -.083a13.3 13.3 0 0 1 4.59 -.08l.456 .08l.396 .083l.161 -.1c1.385 -.84 2.487 -1.17 3.322 -1.148l.164 .008l.147 .017l.076 .014l.05 .011l.144 .047a1 1 0 0 1 .53 .514a5.2 5.2 0 0 1 .397 2.91l-.047 .267l-.046 .196l.123 .163c.574 .795 .93 1.728 1.03 2.707l.023 .295l.007 .272c0 3.855 -1.659 5.883 -4.644 6.68l-.245 .061l-.132 .029l.014 .161l.008 .157l.004 .365l-.002 .213l-.003 3.834a1 1 0 0 1 -.883 .993l-.117 .007h-6a1 1 0 0 1 -.993 -.883l-.007 -.117v-.734c-1.818 .26 -3.03 -.424 -4.11 -1.878l-.535 -.766c-.28 -.396 -.455 -.579 -.589 -.644l-.048 -.019a1 1 0 0 1 .564 -1.918c.642 .188 1.074 .568 1.57 1.239l.538 .769c.76 1.079 1.36 1.459 2.609 1.191l.001 -.678l-.018 -.168a5.03 5.03 0 0 1 -.021 -.824l.017 -.185l.019 -.12l-.108 -.024c-2.976 -.71 -4.703 -2.573 -4.875 -6.139l-.01 -.31l-.004 -.292a5.6 5.6 0 0 1 .908 -3.051l.152 -.222l.122 -.163l-.045 -.196a5.2 5.2 0 0 1 .145 -2.642l.1 -.282l.106 -.253a1 1 0 0 1 .529 -.514l.144 -.047l.154 -.03z"
          strokeWidth="0"
          fill="currentColor"
        ></path>
      </svg>
    ),
  },
  docsRepositoryBase:
    "https://github.com/tum-esm/automated-retrieval-pipeline/blob/main/docs",
  //primaryHue: 43,
  navigation: true,
  useNextSeoProps() {
    return {
      titleTemplate: "%s – EM27 Retrieval Pipeline",
    };
  },
  head: (
    <>
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <meta property="og:title" content="EM27 Retrieval Pipeline" />
      <meta
        property="og:description"
        content="Automated Data Pipeline for EM27/SUN measurement data"
      />
    </>
  ),
  footer: {
    text: (
      <span>
        © TUM Professorship of Environmental Sensing and Modeling,{" "}
        {new Date().getFullYear()}
      </span>
    ),
  },
  faviconGlyph: "🌋",
  sidebar: {
    titleComponent({ title, type, route }) {
      if (type === "doc") {
        if (route.split("/").length <= 2) {
          return (
            <span className="font-semibold text-gray-800 dark:text-gray-200">
              {title}
            </span>
          );
        } else {
          return (
            <span className="text-gray-600 dark:text-gray-400">{title}</span>
          );
        }
      }
    },
  },
  banner: {
    key: "v1.0.0",
    text: "🌈 The EM27 Retrieval Pipeline 1.0.0 has been released",
  },
  toc: {
    float: true,
  },
};
