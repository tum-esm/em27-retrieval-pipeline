import CONFIG_SCHEMA_OBJECT from './config-schema-object';

function renderConfigProperty(
    prefix: string,
    propertyKey: string,
    propertyObject: any,
    required: boolean
) {
    if (!required && propertyObject.default === undefined) {
        propertyObject.default = null;
    }

    const depth = prefix.split('.').length;
    let fontSize: string;
    let subFontSize: string;
    let bgColor: string;
    let dividerColor: string;
    switch (depth) {
        case 1:
            fontSize = 'text-xl';
            subFontSize = 'text-lg';
            bgColor = 'bg-slate-100';
            dividerColor = 'divide-slate-200';
            break;
        case 2:
            fontSize = 'text-lg';
            subFontSize = 'text-md';
            bgColor = 'bg-slate-200';
            dividerColor = 'divide-slate-300';
            break;
        case 3:
            fontSize = 'text-md';
            subFontSize = 'text-sm';
            bgColor = 'bg-slate-300';
            dividerColor = 'divide-slate-400';
            break;
        default:
            fontSize = 'text-sm';
            subFontSize = 'text-xs';
            bgColor = 'bg-slate-400';
            dividerColor = 'divide-slate-500';
            break;
    }
    return (
        <div className={`flex flex-col p-3`}>
            <div className={`font-semibold ${fontSize} leading-tight`}>
                {/*<span className='font-mono text-slate-800/40'>{prefix}.</span>*/}
                <span className='font-mono text-slate-800'>{propertyKey}</span>
                {required && (
                    <span
                        className='px-0.5 rounded text-rose-700'
                        title='required'
                    >
                        *
                    </span>
                )}
                <span className='px-0.5 rounded text-rose-700'>
                    ({propertyObject.type})
                </span>
            </div>
            {propertyObject.description !== undefined && (
                <div className={`mt-1 mb-2 text-slate-700 ${fontSize}`}>
                    {propertyObject.description}
                </div>
            )}
            <div
                className={`flex flex-col leading-tight ${fontSize} text-slate-700`}
            >
                {[
                    ['default', 'default'],
                    ['pattern', 'regex pattern'],
                    ['minLength', 'min. length'],
                    ['maxLength', 'max. length'],
                    ['minimum', 'min.'],
                    ['maximum', 'max.'],
                    ['minItems', 'min. items'],
                    ['maxItems', 'max. items'],
                    ['enum', 'allowed values'],
                ].map(([key, label], b) => (
                    <>
                        {!(key === 'default' && propertyKey === '#') &&
                            propertyObject[key] !== undefined && (
                                <div className='mt-1'>
                                    {label}:{' '}
                                    {JSON.stringify(
                                        propertyObject[key],
                                        null,
                                        1
                                    )}
                                </div>
                            )}
                    </>
                ))}
            </div>

            {['object', 'array'].includes(propertyObject.type) && (
                <div className={`flex flex-col ml-6 rounded ${bgColor} mt-2`}>
                    {propertyObject.type === 'object' && (
                        <div
                            className={`flex flex-col divide-y ${dividerColor}`}
                        >
                            {Object.keys(propertyObject.properties).map(key =>
                                renderConfigProperty(
                                    `${prefix}.${propertyKey}`,
                                    key,
                                    propertyObject.properties[key],
                                    propertyObject.required?.includes(key) ||
                                        false
                                )
                            )}
                        </div>
                    )}
                    {propertyObject.type === 'array' &&
                        renderConfigProperty(
                            `${prefix}.${propertyKey}`,
                            '#',
                            propertyObject.items,
                            false
                        )}
                </div>
            )}
        </div>
    );
}

function ConfigSchema() {
    return (
        <div className='flex flex-col mt-4 gap-y-4 text-slate-950'>
            {Object.keys(CONFIG_SCHEMA_OBJECT.properties).map(key =>
                renderConfigProperty(
                    'config',
                    key,
                    CONFIG_SCHEMA_OBJECT.properties[key],
                    CONFIG_SCHEMA_OBJECT.required.includes(key)
                )
            )}
        </div>
    );
}

export default ConfigSchema;
