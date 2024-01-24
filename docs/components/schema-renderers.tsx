import React from "react";
import CONFIG_SCHEMA_OBJECT from "./config-schema-object";

function renderConfigProperty(
  prefix: string,
  propertyKey: string,
  propertyObject: any,
  required: boolean
) {
  if (!required && propertyObject.default === undefined) {
    propertyObject.default = null;
  }

  const depth = prefix.split(".").length;
  let fontSize: string;
  let bgColor: string;
  let dividerColor: string;
  switch (depth) {
    case 1:
      fontSize = "text-xl";
      bgColor = "bg-slate-100 dark:bg-slate-800";
      dividerColor = "divide-slate-200 dark:divide-slate-700";
      break;
    case 2:
      fontSize = "text-lg";
      bgColor = "bg-slate-200 dark:bg-slate-700";
      dividerColor = "divide-slate-300 dark:divide-slate-600";
      break;
    case 3:
      fontSize = "text-md";
      bgColor = "bg-slate-300 dark:bg-slate-600";
      dividerColor = "divide-slate-400 dark:divide-slate-500";
      break;
    default:
      fontSize = "text-sm";
      bgColor = "bg-slate-400 dark:bg-slate-500";
      dividerColor = "divide-slate-500 dark:divide-slate-400";
      break;
  }
  return (
    <div className={`flex flex-col p-3`} key={propertyKey}>
      <div className={`font-semibold ${fontSize} leading-tight`}>
        {/*<span className='font-mono text-slate-800/40'>{prefix}.</span>*/}
        <span className="font-mono text-slate-800 dark:text-slate-200">
          {propertyKey}
        </span>
        {required && (
          <span
            className="px-0.5 rounded text-rose-700 dark:text-rose-300"
            title="required"
          >
            *
          </span>
        )}
        <span className="px-0.5 rounded text-rose-700 dark:text-rose-300">
          ({propertyObject.type})
        </span>
      </div>
      {propertyObject.description !== undefined && (
        <div
          className={`mt-1 mb-2 ${fontSize} text-slate-700 dark:text-slate-300`}
        >
          {propertyObject.description}
        </div>
      )}
      <div
        className={`flex flex-col leading-tight ${fontSize} text-slate-700 dark:text-slate-300`}
      >
        {[
          ["default", "default"],
          ["pattern", "regex pattern"],
          ["minLength", "min. length"],
          ["maxLength", "max. length"],
          ["minimum", "min."],
          ["maximum", "max."],
          ["minItems", "min. items"],
          ["maxItems", "max. items"],
          ["enum", "allowed values"],
        ].map(([key, label], index) => (
          <React.Fragment key={index}>
            {!(key === "default" && propertyKey === "#") &&
              propertyObject[key] !== undefined && (
                <div className="mt-1">
                  {label}: {JSON.stringify(propertyObject[key], null, 1)}
                </div>
              )}
          </React.Fragment>
        ))}
      </div>

      {["object", "array"].includes(propertyObject.type) && (
        <div className={`flex flex-col ml-6 rounded ${bgColor} mt-2`}>
          {propertyObject.type === "object" && (
            <div className={`flex flex-col divide-y ${dividerColor}`}>
              {Object.keys(propertyObject.properties).map((key) =>
                renderConfigProperty(
                  `${prefix}.${propertyKey}`,
                  key,
                  propertyObject.properties[key],
                  propertyObject.required?.includes(key) || false
                )
              )}
            </div>
          )}
          {propertyObject.type === "array" &&
            renderConfigProperty(
              `${prefix}.${propertyKey}`,
              "#",
              propertyObject.items,
              false
            )}
        </div>
      )}
    </div>
  );
}

export function ConfigSchema() {
  return (
    <div className="flex flex-col mt-4 gap-y-4 text-slate-950">
      {Object.keys(CONFIG_SCHEMA_OBJECT.properties).map((key) =>
        renderConfigProperty(
          "config",
          key,
          CONFIG_SCHEMA_OBJECT.properties[key],
          CONFIG_SCHEMA_OBJECT.required.includes(key)
        )
      )}
    </div>
  );
}
