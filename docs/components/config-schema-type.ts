import { z } from 'zod';

const ZodEndObject = z.object({
    title: z.string(),
    description: z.string().optional(),
    type: z.literal('object'),
    properties: z.record(
        z.string(),
        z.union([
            z.object({
                title: z.string(),
                type: z.literal('string'),
                description: z.string().optional(),
                enum: z.array(z.string()).optional(),
                default: z.string().optional(),
                minLength: z.number().optional(),
                maxLength: z.number().optional(),
                pattern: z.string().optional(),
            }),
            z.object({
                title: z.string(),
                type: z.literal('integer'),
                description: z.string().optional(),
                default: z.number().optional(),
                minimum: z.number().optional(),
                maximum: z.number().optional(),
            }),
            z.object({
                title: z.string(),
                description: z.string().optional(),
                type: z.literal('boolean'),
            }),
            z.object({
                title: z.string(),
                type: z.literal('array'),
                description: z.string().optional(),
                default: z.array(z.any()).optional(),
                minItems: z.number().optional(),
                maxItems: z.number().optional(),
                items: z.object({
                    type: z.literal('string'),
                    enum: z.array(z.string()).optional(),
                }),
            }),
        ])
    ),
    required: z.array(z.string()),
});

const ZodConfigObject = z.object({
    title: z.literal('Config'),
    description: z.string().optional(),
    type: z.literal('object'),
    properties: z.record(
        z.string(),
        z.union([
            z.object({
                title: z.string(),
                description: z.string().optional(),
                type: z.literal('object'),
                properties: z.record(z.string(), ZodEndObject),
                required: z.array(z.string()),
            }),
            z.object({
                title: z.string(),
                type: z.literal('array'),
                default: z.array(z.any()).optional(),
                minItems: z.number().optional(),
                maxItems: z.number().optional(),
                items: ZodEndObject,
            }),
        ])
    ),
    required: z.array(z.string()),
    definitions: z.any().optional(),
});

type ZodConfigType = z.infer<typeof ZodConfigObject>;

export default ZodConfigType;
