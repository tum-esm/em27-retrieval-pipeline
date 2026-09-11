import RefParser from "@apidevtools/json-schema-ref-parser";

type ObjectSchema = {
  type: "object";
  additionalProperties: AnySchema;
  description?: string;
  required?: string[];
  title: string;
  properties: Record<string, AnySchema>;
  introduced_in_version?: string;
  examples?: any[];
};

type ConstantSchema = {
  type: "string" | "number" | "boolean";
  const: string | number | boolean;
  title: string;
  introduced_in_version?: string;
  description?: string;
};

type UnionSchema = {
  anyOf: AnySchema[];
  default: any;
  introduced_in_version?: string;
};

type StringSchema = {
  type: "string";
  title: string;
  description?: string;
  minLength?: number;
  maxLength?: number;
  default?: string;
  pattern?: string;
  examples?: string[];
  enum?: string[];
  introduced_in_version?: string;
};

type EnumSchema = {
  title: string;
  description?: string;
  default?: any;
  examples?: string[];
  enum?: any[];
  introduced_in_version?: string;
};

type IntegerSchema = {
  type: "integer";
  title: string;
  description?: string;
  minimum?: number;
  maximum?: number;
  default?: number;
  unit?: string;
  introduced_in_version?: string;
};

type FloatSchema = {
  type: "number";
  description?: string;
  minimum?: number;
  maximum?: number;
  default?: number;
  unit?: string;
  introduced_in_version?: string;
};

type ArraySchema = {
  type: "array";
  title: string;
  description?: string;
  items: AnySchema;
  examples?: any[];
  minItems?: number;
  maxItems?: number;
  introduced_in_version?: string;
};

type NullSchema = {
  type: "null";
  introduced_in_version?: string;
};

type BooleanSchema = {
  type: "boolean";
  default: boolean;
  description?: string;
  title: string;
  introduced_in_version?: string;
};

type AnySchema =
  | ObjectSchema
  | ConstantSchema
  | UnionSchema
  | StringSchema
  | IntegerSchema
  | FloatSchema
  | ArraySchema
  | NullSchema
  | BooleanSchema
  | EnumSchema;

async function ShallowSchema(props: {
  schema: AnySchema;
  path?: string;
  required?: boolean;
  className?: string;
}) {
  let schema: AnySchema = await RefParser.dereference(props.schema);

  if (props.path !== undefined) {
    const parts = props.path.split(".");
    for (const part of parts) {
      schema = (schema as any)[part];
    }
  }

  // assert schema is object
  if (schema.type !== "object") {
    return "";
  }
  if (!("properties" in schema)) {
    return "";
  }

  // now loop through the sorted properties and render them (only title and type for now)
  return (
    <div className="flex flex-col items-start gap-y-6 not-content">
      {Object.entries(schema.properties).map(([key, value]) => {
        return (
          <div className="flex flex-col items-start justify-start gap-y-0.5 w-full pl-4 text-sm" key={key}>
            <div className="flex flex-row items-baseline justify-start w-full gap-x-2 -ml-4">
              <div className="font-semibold text-slate-900 dark:text-slate-50">
                {key}
              </div>
              <div className="font-medium text-blue-600 dark:text-blue-400">
                [
                {value.type ? (Array.isArray(value.type)
                  ? value.type.join(" | ")
                  : value.type) : "predefined options"}
                ]
              </div>
              <div className="">
                {schema.required?.includes(key) && (
                  <span
                    className="text-accent-600 dark:text-accent-400 font-semibold"
                    title="required"
                  >
                    * required
                  </span>
                )}
              </div>
              {value.introduced_in_version && (
                <div className="ml-auto text-xs text-slate-500 dark:text-slate-400">
                  introduced in version {value.introduced_in_version}
                </div>
              )}
            </div>
            <p>{value.description}</p>
            {value.default !== undefined && (
              <p>
                <span className="font-semibold">Default:</span>{" "}
                {JSON.stringify(value.default, null, 2)}
              </p>
            )}
            {value.examples && (
              <div className="flex flex-row gap-x-2">
                <span className="font-semibold">Examples:</span>{" "}
                <div className="flex flex-col">
                  {value.examples.map((v, i) => (
                    <div key={i} className="">
                      - {JSON.stringify(v, null, 2)}
                    </div>
                  ))}
                </div>
              </div>
            )}
            {value.enum && (
              <div className="flex flex-row gap-x-2">
                <span className="font-semibold">Allowed values:</span>
                <div className="flex flex-col">
                  {value.enum.map((v, i) => (
                    <div key={i} className="">
                      - {JSON.stringify(v)}
                    </div>
                  ))}
                </div>
              </div>
            )}
            {value.minimum !== undefined && (
              <p>
                <span className="font-semibold">Minimum:</span> {value.minimum}
              </p>
            )}
            {value.maximum !== undefined && (
              <p>
                <span className="font-semibold">Maximum:</span> {value.maximum}
              </p>
            )}
            {value.pattern !== undefined && (
              <p>
                <span className="font-semibold">Regex Pattern:</span> "
                {value.pattern}"
              </p>
            )}
            {value.unit !== undefined && (
              <p>
                <span className="font-semibold">Unit:</span> {value.unit}
              </p>
            )}
            {value.minLength !== undefined && (
              <p>
                <span className="font-semibold">Min. Length:</span>{" "}
                {value.minLength}
              </p>
            )}
            {value.maxLength !== undefined && (
              <p>
                <span className="font-semibold">Max. Length:</span>{" "}
                {value.maxLength}
              </p>
            )}
            {value.minItems !== undefined && (
              <p>
                <span className="font-semibold">Min. Items:</span>{" "}
                {value.minItems}
              </p>
            )}
            {value.maxItems !== undefined && (
              <p>
                <span className="font-semibold">Max. Items:</span>{" "}
                {value.maxItems}
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}

async function Schema(props: {
  schema: AnySchema;
  path?: string;
  required?: boolean;
  className?: string;
}) {
  let schema: AnySchema = await RefParser.dereference(props.schema);
  if (props.path !== undefined) {
    const parts = props.path.split(".");
    for (const part of parts) {
      schema = (schema as any)[part];
    }
  }

  const title = (label: string) => (
    <p>
      <span className="text-base font-semibold">{props.name} </span>
      {props.required && (
        <span className="text-rose-600 font-bold" title="required">
          *
        </span>
      )}{" "}
      <span className="text-rose-600 font-bold text-sm">({label})</span>
    </p>
  );
  const body = (
    <>
      {"description" in schema && <p>{schema.description}</p>}
      {"pattern" in schema && (
        <p>
          <span className="font-semibold">Regex Pattern:</span> "
          {schema.pattern}"
        </p>
      )}
      {"minLength" in schema && (
        <p>
          <span className="font-semibold">Min. Length:</span> {schema.minLength}
        </p>
      )}
      {"maxLength" in schema && (
        <p>
          <span className="font-semibold">Max. Length:</span> {schema.maxLength}
        </p>
      )}
      {"minItems" in schema && (
        <p>
          <span className="font-semibold">Min. Items:</span> {schema.minItems}
        </p>
      )}
      {"maxItems" in schema && (
        <p>
          <span className="font-semibold">Max. Items:</span> {schema.maxItems}
        </p>
      )}
      {"minimum" in schema && (
        <p>
          <span className="font-semibold">Minimum:</span> {schema.minimum}
        </p>
      )}
      {"maximum" in schema && (
        <p>
          <span className="font-semibold">Maximum:</span> {schema.maximum}
        </p>
      )}
      {"default" in schema && (
        <p>
          <span className="font-semibold">Default:</span>{" "}
          {JSON.stringify(schema.default, null, 2)}
        </p>
      )}
      {"examples" in schema && (
        <p>
          <span className="font-semibold">Examples:</span>{" "}
          {JSON.stringify(schema.examples, null, 2)}
        </p>
      )}
      {"enum" in schema && (
        <p>
          <span className="font-semibold">Allowed values:</span>{" "}
          <div className="whitespace-pre">
            {JSON.stringify(schema.enum, null, 2)}
          </div>
        </p>
      )}
      {"unit" in schema && (
        <p>
          <span className="font-semibold">Unit:</span> {schema.unit}
        </p>
      )}
    </>
  );

  const boxSchema = `border px-3 py-3 flex flex-col space-y-2 m-0 text-sm bg-slate-300/25 border-slate-600/30 dark:bg-slate-700/20 dark:border-slate-400/30 text-slate-950 dark:text-slate-50 rounded-lg ${props.className}`;

  if ("anyOf" in schema) {
    return (
      <div className={boxSchema}>
        {title("union")}
        {body}
        <p className="font-semibold">Options:</p>
        {schema.anyOf?.map((s, i) => (
          <Schema
            schema={s}
            name={`#${i + 1}`}
            className={
              "!mt-0 !-mb-px rounded-none" +
              (i === 0 ? " !rounded-t-lg !mt-2" : "") +
              (i === schema.anyOf.length - 1 ? " !rounded-b-lg" : "")
            }
          />
        ))}
      </div>
    );
  } else if ("const" in schema) {
    return (
      <div className={boxSchema}>
        {title("constant")}
        {body}
      </div>
    );
  } else if (schema.type === "object") {
    const required = schema.required || [];
    return (
      <div className={boxSchema}>
        {title("object")}
        {body}
        {schema.properties &&
          Object.entries(schema.properties).map(([key, value], i) => (
            <Schema
              schema={value}
              name={key}
              key={key}
              required={required.includes(key)}
              className={
                "!mt-0 !-mb-px rounded-none" +
                (i === 0 ? " !rounded-t-lg !mt-2" : "") +
                (i === Object.keys(schema.properties).length - 1
                  ? " !rounded-b-lg"
                  : "")
              }
            />
          ))}
        {schema.additionalProperties && (
          <div>
            <p className="font-semibold">Key Schema:</p>
            <Schema schema={schema.additionalProperties} name="#" />
          </div>
        )}
      </div>
    );
  } else if (schema.type === "array") {
    return (
      <div className={boxSchema}>
        {title("array")}
        {body}
        <p className="font-semibold">Key Schema:</p>
        <Schema schema={schema.items} name="#" />
      </div>
    );
  } else if (schema.type === "string") {
    return (
      <div className={boxSchema}>
        {title("string")}
        {body}
      </div>
    );
  } else if (schema.type === "number") {
    return (
      <div className={boxSchema}>
        {title("number")}
        {body}
      </div>
    );
  } else if (schema.type === "integer") {
    return (
      <div className={boxSchema}>
        {title("integer")}
        {body}
      </div>
    );
  } else if (schema.type === "boolean") {
    return (
      <div className={boxSchema}>
        {title("boolean")}
        {body}
      </div>
    );
  } else if (schema.type === "null") {
    return (
      <div className={boxSchema}>
        {title("null")}
        {body}
      </div>
    );
  }
}

export default function JSONSchemaRenderer(props: {
  schema: AnySchema;
  path?: string;
}) {
  return <ShallowSchema schema={props.schema} path={props.path} />;
}
