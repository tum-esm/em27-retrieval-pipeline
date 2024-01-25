import React from "react";
import CONFIG_SCHEMA from "./config-schema";
import LOCATIONS_SCHEMA from "./locations-schema";
import SENSORS_SCHEMA from "./sensors-schema";
import CAMPAIGNS_SCHEMA from "./campaigns-schema";

const COLORS: {
  [key in number]: string;
} = {
  0: "text-[17px]",
  1: "text-[16px]",
  2: "text-[15px]",
  3: "text-[14px]",
  4: "text-[13px]",
  5: "text-[12px]",
  6: "text-[11px]",
  7: "text-[10px]",
  8: "text-[9px]",
};

const CONTAINER_CLASSES =
  "border border-slate-300 dark:border-slate-700 rounded first:rounded-t-lg last:rounded-b-lg";

function ObjectTitle(props: { name: string; required: boolean; type: string }) {
  return (
    <div className={`font-semibold leading-tight mb-0.5`}>
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
    <div className={`${props.className || ""} p-4 flex flex-col gap-y-1`}>
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
    <div className={`${props.className || ""} p-4 flex flex-col gap-y-1`}>
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
    <div className={`${props.className || ""} p-4 flex flex-col gap-y-1`}>
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
    <div className={`${props.className || ""} p-4 flex flex-col gap-y-1`}>
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
    <div className={`${props.className || ""} p-4 flex flex-col gap-y-1`}>
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
      <div className={`${COLORS[depth]} ${CONTAINER_CLASSES}`}>
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
      <div className={`${COLORS[depth]} ${CONTAINER_CLASSES}`}>
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
      <div className={`${COLORS[depth]} ${CONTAINER_CLASSES}`}>
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
      <div className={`${COLORS[depth]} ${CONTAINER_CLASSES}`}>
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
      <div className={`${COLORS[depth]} ${CONTAINER_CLASSES}`}>
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
      <div
        className={`flex flex-col p-4 gap-y-2 ${COLORS[depth]} ${CONTAINER_CLASSES}`}
      >
        <ObjectTitle
          name={propertyKey}
          required={propertyObject}
          type="union"
        />
        <ObjectDescription text={propertyObject.description} />
        <div className={`flex flex-col rounded-lg mt-2`}>
          <div className={`flex flex-col gap-y-1`}>
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
      <div
        className={`flex flex-col p-4 gap-y-1 ${COLORS[depth]} ${CONTAINER_CLASSES}`}
      >
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
          <div className={`flex flex-col gap-y-1 rounded-lg mt-2`}>
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
      <div
        className={`flex flex-col p-4 gap-y-2 ${COLORS[depth]} ${CONTAINER_CLASSES}`}
      >
        <ObjectTitle name={propertyKey} required={required} type="array" />
        <ObjectDescription text={propertyObject.description} />
        <ObjectAttributeList
          consideredAttributes={["default", "examples"]}
          object={propertyObject}
        />
        <div className={`flex flex-col gap-y-2 rounded-lg mt-2`}>
          <div className={`flex flex-col`}>
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
    <div className={`flex flex-col mt-4 rounded-lg gap-y-2 text-slate-950`}>
      {renderConfigProperty(1, "root", props.schema, true)}
    </div>
  );
}

export function ConfigSchema() {
  return <Schema schema={CONFIG_SCHEMA} />;
}

export function LocationsSchema() {
  return <Schema schema={LOCATIONS_SCHEMA} />;
}

export function SensorsSchema() {
  return <Schema schema={SENSORS_SCHEMA} />;
}

export function CampaignsSchema() {
  return <Schema schema={CAMPAIGNS_SCHEMA} />;
}
