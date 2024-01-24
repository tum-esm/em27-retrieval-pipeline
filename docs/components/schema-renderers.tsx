import React from "react";
import CONFIG_SCHEMA from "./config-schema";

const COLORS: {
  [key in number]: { text: string; panel: string; divider: string };
} = {
  0: {
    text: "text-[17px]",
    panel:
      "bg-balancedSlate-50 dark:bg-balancedSlate-900 border border-balancedSlate-150 dark:border-balancedSlate-800",
    divider: "divide-balancedSlate-150 dark:divide-balancedSlate-800",
  },
  1: {
    text: "text-[16px]",
    panel:
      "bg-balancedSlate-100 dark:bg-balancedSlate-850 border border-balancedSlate-200 dark:border-balancedSlate-750",
    divider: "divide-balancedSlate-200 dark:divide-balancedSlate-750",
  },
  2: {
    text: "text-[15px]",
    panel:
      "bg-balancedSlate-150 dark:bg-balancedSlate-800 border border-balancedSlate-250 dark:border-balancedSlate-700",
    divider: "divide-balancedSlate-250 dark:divide-balancedSlate-700",
  },
  3: {
    text: "text-[14px]",
    panel:
      "bg-balancedSlate-200 dark:bg-balancedSlate-750 border border-balancedSlate-300 dark:border-balancedSlate-650",
    divider: "divide-balancedSlate-300 dark:divide-balancedSlate-650",
  },
  4: {
    text: "text-[13px]",
    panel:
      "bg-balancedSlate-250 dark:bg-balancedSlate-700 border border-balancedSlate-350 dark:border-balancedSlate-600",
    divider: "divide-balancedSlate-350 dark:divide-balancedSlate-600",
  },
  5: {
    text: "text-[12px]",
    panel:
      "bg-balancedSlate-300 dark:bg-balancedSlate-650 border border-balancedSlate-400 dark:border-balancedSlate-550",
    divider: "divide-balancedSlate-400 dark:divide-balancedSlate-550",
  },
  6: {
    text: "text-[11px]",
    panel:
      "bg-balancedSlate-350 dark:bg-balancedSlate-600 border border-balancedSlate-450 dark:border-balancedSlate-500",
    divider: "divide-balancedSlate-450 dark:divide-balancedSlate-500",
  },
  7: {
    text: "text-[10px]",
    panel:
      "bg-balancedSlate-400 dark:bg-balancedSlate-550 border border-balancedSlate-500 dark:border-balancedSlate-450",
    divider: "divide-balancedSlate-500 dark:divide-balancedSlate-450",
  },
  8: {
    text: "text-[9px]",
    panel:
      "bg-balancedSlate-450 dark:bg-balancedSlate-500 border border-balancedSlate-550 dark:border-balancedSlate-400",
    divider: "divide-balancedSlate-550 dark:divide-balancedSlate-400",
  },
};

function ObjectTitle(props: { name: string; required: boolean; type: string }) {
  return (
    <div className={`font-semibold leading-tight`}>
      <span className="font-bold text-slate-950 dark:text-slate-100">
        {props.name}
      </span>
      {props.required && (
        <span
          className="px-0.5 text-rose-700 dark:text-rose-300"
          title="required"
        >
          *
        </span>
      )}
      <span className="px-0.5 text-rose-700 dark:text-rose-300">
        ({props.type})
      </span>
    </div>
  );
}

function ObjectDescription(props: { text: string | null | undefined }) {
  if (props.text === undefined || props.text === null) {
    return null;
  }
  return (
    <div className={`text-slate-800 dark:text-slate-300 leading-tight`}>
      {props.text}
    </div>
  );
}

function ObjectAttribute(props: { name: string; value: any }) {
  const knownAttributes = {
    examples: "examples",
    default: "default",
    pattern: "regex pattern",
    minLength: "min. length",
    maxLength: "max. length",
    minimum: "min.",
    maximum: "max.",
    minItems: "min. items",
    maxItems: "max. items",
    const: "allowed value",
    enum: "allowed values",
  };
  if (
    props.name in knownAttributes &&
    props.value !== undefined &&
    props.value !== null
  ) {
    return (
      <div className={`text-slate-800 dark:text-slate-300`}>
        {knownAttributes[props.name]}: {JSON.stringify(props.value, null, 4)}
      </div>
    );
  } else {
    return null;
  }
}

function ObjectAttributeList(props: {
  consideredAttributes: string[];
  object: any;
}) {
  const attributes: { name: string; value: any }[] = [];

  props.consideredAttributes.forEach((name) => {
    if (name in props.object && props.object[name] !== null) {
      attributes.push({ name, value: props.object[name] });
    }
  });
  //return JSON.stringify(attributes, null, 4);
  if (attributes.length === 0) {
    return null;
  } else {
    return (
      <div className="flex flex-col gap-y-0">
        {attributes.map((attribute) => (
          <ObjectAttribute name={attribute.name} value={attribute.value} />
        ))}
      </div>
    );
  }
}

function ConstProperty(props: {
  name: string;
  value: any;
  className?: string;
  required: boolean;
}) {
  return (
    <div className={`${props.className} p-4 flex flex-col gap-y-2`}>
      <ObjectTitle
        name={props.name}
        required={props.required}
        type="constant"
      />
      <ObjectDescription text={props.value.description} />
      <ObjectAttributeList
        consideredAttributes={["const"]}
        object={props.value}
      />
    </div>
  );
}

function NullProperty(props: {
  name: string;
  value: any;
  className?: string;
  required: boolean;
}) {
  return (
    <div className={`${props.className} p-4 flex flex-col gap-y-2`}>
      <ObjectTitle name={props.name} required={props.required} type="null" />
    </div>
  );
}

function EnumProperty(props: {
  name: string;
  value: any;
  className?: string;
  required: boolean;
}) {
  return (
    <div className={`${props.className} p-4 flex flex-col gap-y-2`}>
      <ObjectTitle name={props.name} required={props.required} type="enum" />
      <ObjectDescription text={props.value.description} />
      <ObjectAttributeList
        consideredAttributes={["enum", "default"]}
        object={props.value}
      />
    </div>
  );
}

function StringProperty(props: {
  name: string;
  value: any;
  className?: string;
  required: boolean;
}) {
  return (
    <div className={`${props.className} p-4 flex flex-col gap-y-2`}>
      <ObjectTitle name={props.name} required={props.required} type="string" />
      <ObjectDescription text={props.value.description} />
      <ObjectAttributeList
        consideredAttributes={[
          "minLength",
          "maxLength",
          "pattern",
          "default",
          "examples",
        ]}
        object={props.value}
      />
    </div>
  );
}

function NumberProperty(props: {
  name: string;
  value: any;
  className?: string;
  required: boolean;
}) {
  return (
    <div className={`${props.className} p-4 flex flex-col gap-y-2`}>
      <ObjectTitle
        name={props.name}
        required={props.required}
        type={props.value.type}
      />
      <ObjectDescription text={props.value.description} />
      <ObjectAttributeList
        consideredAttributes={["minimum", "maximum", "default", "examples"]}
        object={props.value}
      />
    </div>
  );
}

function renderConfigProperty(
  depth: number,
  propertyKey: string,
  propertyObject: any,
  required: boolean
) {
  if (!required && propertyObject.default === undefined) {
    propertyObject.default = null;
  }

  if ("const" in propertyObject) {
    console.log({ propertyKey, propertyObject });
    return (
      <div className={COLORS[depth].text}>
        <ConstProperty
          name={propertyKey}
          value={propertyObject}
          required={required}
        />
      </div>
    );
  }
  if ("enum" in propertyObject) {
    console.log({ propertyKey, propertyObject });
    return (
      <div className={COLORS[depth].text}>
        <EnumProperty
          name={propertyKey}
          value={propertyObject}
          required={required}
        />
      </div>
    );
  }
  if (propertyObject.type === "string") {
    return (
      <div className={COLORS[depth].text}>
        <StringProperty
          name={propertyKey}
          value={propertyObject}
          required={required}
        />
      </div>
    );
  }
  if (
    propertyObject.type === "number" ||
    propertyObject.type === "integer" ||
    propertyObject.type === "float"
  ) {
    return (
      <div className={COLORS[depth].text}>
        <NumberProperty
          name={propertyKey}
          value={propertyObject}
          required={required}
        />
      </div>
    );
  }
  if (propertyObject.type === "null") {
    return (
      <div className={COLORS[depth].text}>
        <NullProperty
          name={propertyKey}
          value={propertyObject}
          required={required}
        />
      </div>
    );
  }

  // union
  if (propertyObject.anyOf) {
    return (
      <div className={`flex flex-col p-4 gap-y-2 ${COLORS[depth].text}`}>
        <ObjectTitle
          name={propertyKey}
          required={propertyObject}
          type="union"
        />
        <ObjectDescription text={propertyObject.description} />
        <div className={`flex flex-col rounded-lg ${COLORS[depth].panel} mt-2`}>
          <div className={`flex flex-col divide-y ${COLORS[depth].divider}`}>
            {propertyObject.anyOf.map((option: any, i: number) =>
              renderConfigProperty(depth + 1, `option ${i + 1}`, option, false)
            )}
          </div>
        </div>
      </div>
    );
  }

  // object
  if (propertyObject.type === "object") {
    return (
      <div className={`flex flex-col p-4 gap-y-2 ${COLORS[depth].text}`}>
        <ObjectTitle name={propertyKey} required={required} type="object" />
        <ObjectDescription text={propertyObject.description} />
        <div className="text-slate-800 dark:text-slate-300">
          additional properties allowed:{" "}
          {JSON.stringify(
            propertyObject.additionalProperties === true ||
              !propertyObject.properties
          )}
        </div>
        {propertyObject.properties && (
          <div
            className={`flex flex-col gap-y-2 rounded-lg ${COLORS[depth].panel} mt-2 divide-y ${COLORS[depth].divider}`}
          >
            {Object.keys(propertyObject.properties).map((key) =>
              renderConfigProperty(
                depth + 1,
                key,
                propertyObject.properties[key],
                propertyObject.required?.includes(key) || false
              )
            )}
          </div>
        )}
        {!propertyObject.properties && (
          <div className="text-slate-800 dark:text-slate-300">
            no schema enforced
          </div>
        )}
      </div>
    );
  }

  // array
  if (propertyObject.type === "array") {
    return (
      <div className={`flex flex-col p-4 gap-y-2 ${COLORS[depth].text}`}>
        <ObjectTitle name={propertyKey} required={required} type="array" />
        <ObjectDescription text={propertyObject.description} />
        <ObjectAttributeList
          consideredAttributes={["default", "examples"]}
          object={propertyObject}
        />
        <div
          className={`flex flex-col gap-y-2 rounded-lg ${COLORS[depth].panel} mt-2`}
        >
          <div className={`flex flex-col divide-y ${COLORS[depth].divider}`}>
            {renderConfigProperty(depth + 1, "#", propertyObject.items, false)}
          </div>
        </div>
      </div>
    );
  }

  console.log(`could not render property: ${propertyKey}: ${propertyObject}`);
  return null;
}

function Schema(props: { schema: any }) {
  return (
    <div
      className={`flex flex-col mt-4 rounded-lg gap-y-2 text-slate-950 ${COLORS[0].panel}`}
    >
      {renderConfigProperty(1, "root", props.schema, true)}
    </div>
  );
}

export function ConfigSchema() {
  return <Schema schema={CONFIG_SCHEMA} />;
}
