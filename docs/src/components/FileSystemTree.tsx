import { IconFolderFilled, IconFile } from "@tabler/icons-react";

type FileSchema = {
  type: "file";
  title: string;
  providedByDownload?: boolean;
  providedByUser?: boolean;
  optional?: boolean;
  required?: boolean;
  description?: string;
};
type DirectorySchema = {
  type: "directory";
  title: string;
  providedByDownload?: boolean;
  providedByUser?: boolean;
  optional?: boolean;
  required?: boolean;
  description?: string;
  items?: (FileSchema | DirectorySchema)[];
};

async function ItemHeader(props: {
  variant: "file" | "directory";
  title: string;
  providedByDownload?: boolean;
  providedByUser?: boolean;
  optional?: boolean;
  required?: boolean;
  description?: string;
}) {
  return (
    <div className="flex flex-col items-start justify-start gap-y-0 w-full !m-0">
      <div className="flex flex-row items-center justify-start gap-x-0 text-sm h-5 mt-0 w-full">
        {props.variant === "file" && (
          <>
            <div className="w-6 text-slate-600 dark:text-slate-400">
              <IconFile size={18} />
            </div>
            <div className="!m-0 font-medium">{props.title}</div>
          </>
        )}
        {props.variant === "directory" && (
          <>
            <div className="w-6 text-slate-600 dark:text-slate-400">
              <IconFolderFilled size={18} />
            </div>
            <div className="!m-0 font-bold">{props.title}</div>
          </>
        )}
        {props.providedByDownload && (
          <div
            className={
              "!ml-2 text-xs font-medium italic !m-0 py-[0.0625rem] px-1 rounded-md " +
              "bg-yellow-100 text-yellow-600 dark:bg-yellow-700 dark:text-yellow-200"
            }
          >
            provided by download script
          </div>
        )}
        {props.providedByUser && (
          <div
            className={
              "!ml-2 text-xs font-medium  italic !m-0 py-[0.0625rem] px-1 rounded-md " +
              "bg-teal-100 text-teal-600 dark:bg-teal-700 dark:text-teal-200"
            }
          >
            provided by user
          </div>
        )}
        {props.optional && (
          <div
            className={
              "!ml-2 text-xs font-medium italic !m-0 py-[0.0625rem] px-1 rounded-md " +
              "bg-sky-100 text-sky-600 dark:bg-sky-700 dark:text-sky-200"
            }
          >
            optional
          </div>
        )}
        {props.required && (
          <div
            className={
              "!ml-2 text-xs font-medium italic !m-0 py-[0.0625rem] px-1 rounded-md " +
              "bg-rose-100 text-rose-600 dark:bg-rose-700 dark:text-rose-200"
            }
          >
            required
          </div>
        )}
      </div>
      {props.description && (
        <div
          className={
            "text-xs leading-normal !m-0 !ml-2 pl-4 !mt-0.5 " +
            "text-slate-700 dark:text-slate-300 border-slate-300 dark:border-slate-600" +
            (props.variant === "directory" ? " border-l" : "")
          }
        >
          {props.description}
        </div>
      )}
    </div>
  );
}

async function FileComponent(props: { schema: FileSchema }) {
  return (
    <div className="flex flex-col items-start justify-start gap-y-0 w-full">
      <ItemHeader
        variant="file"
        title={props.schema.title}
        providedByDownload={props.schema.providedByDownload}
        providedByUser={props.schema.providedByUser}
        optional={props.schema.optional}
        required={props.schema.required}
        description={props.schema.description}
      />
    </div>
  );
}

async function DirectoryComponent(props: { schema: DirectorySchema }) {
  return (
    <div className="flex flex-col gap-y-0 w-full">
      <ItemHeader
        variant="directory"
        title={props.schema.title}
        providedByDownload={props.schema.providedByDownload}
        providedByUser={props.schema.providedByUser}
        optional={props.schema.optional}
        required={props.schema.required}
        description={props.schema.description}
      />
      {props.schema.items && (
        <div className="flex flex-col !ml-2 pl-4 gap-y-2 !m-0 !pt-2 border-l border-slate-300 dark:border-slate-600">
          {props.schema.items.map((item, i) => (
            <div key={i} className="!m-0">
              {item.type === "file" ? (
                <FileComponent schema={item} />
              ) : (
                <DirectoryComponent schema={item} />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function FileSystemTree(props: { schema: DirectorySchema }) {
  return (
    <div className="bg-slate-50 dark:bg-slate-800 border p-4 rounded-lg text-slate-900 dark:text-slate-100 border-slate-300 dark:border-slate-700">
      <DirectoryComponent schema={props.schema} />
    </div>
  );
}
