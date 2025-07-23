import RefParser from "@apidevtools/json-schema-ref-parser";

type ObjectSchema = {
  type: "object";
  additionalProperties: AnySchema;
  description?: string;
  required?: string[];
  title: string;
  properties: Record<string, AnySchema>;
  examples?: any[];
};

type ConstantSchema = {
  type: "string" | "number" | "boolean";
  const: string | number | boolean;
  title: string;
  description?: string;
};

type UnionSchema = {
  anyOf: AnySchema[];
  default: any;
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
};

type IntegerSchema = {
  type: "integer";
  title: string;
  description?: string;
  minimum?: number;
  maximum?: number;
  default?: number;
  unit?: string;
};

type FloatSchema = {
  type: "number";
  description?: string;
  minimum?: number;
  maximum?: number;
  default?: number;
  unit?: string;
};

type ArraySchema = {
  type: "array";
  title: string;
  description?: string;
  items: AnySchema;
  examples?: any[];
  minItems?: number;
  maxItems?: number;
};

type NullSchema = {
  type: "null";
};

type BooleanSchema = {
  type: "boolean";
  default: boolean;
  description?: string;
  title: string;
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
  | BooleanSchema;

async function Schema(props: {
  schema: AnySchema;
  name: string;
  required?: boolean;
  className?: string;
}) {
  const schema: AnySchema = await RefParser.dereference(props.schema);
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
          {JSON.stringify(schema.enum, null, 2)}
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

export default function JSONSchemaRenderer(props: { schema: AnySchema }) {
  return <Schema schema={props.schema} name="root" />;
}
