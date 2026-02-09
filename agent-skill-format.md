# Agent Skill Format

## Overview

This document defines the standard format for documenting agent skills in the veriloga-skills repository. Each skill should be documented as a markdown file following this structure.

## Structure Template

```markdown
# [Skill Name]

## Metadata
- **Skill ID**: `unique-skill-identifier`
- **Version**: `1.0.0`
- **Category**: `[category-name]` (e.g., data-processing, code-generation, analysis)
- **Last Updated**: `YYYY-MM-DD`
- **Status**: `[active|deprecated|experimental]`

## Description

A clear, concise description of what the skill does and when it should be used.

## Capabilities

List the specific capabilities and features of this skill:

- Capability 1: Description
- Capability 2: Description
- Capability 3: Description

## Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| param1 | string | Yes | - | Description of parameter 1 |
| param2 | number | No | 0 | Description of parameter 2 |
| param3 | boolean | No | false | Description of parameter 3 |

## Output Format

Describe the expected output format:

```json
{
  "result": "description of result",
  "metadata": {
    "timestamp": "ISO-8601 datetime",
    "status": "success|failure"
  }
}
```

## Usage Examples

### Example 1: Basic Usage

**Input:**
```
[Example input data or command]
```

**Output:**
```
[Expected output]
```

### Example 2: Advanced Usage

**Input:**
```
[More complex example input]
```

**Output:**
```
[Expected output]
```

## Prerequisites

- Requirement 1
- Requirement 2
- Required dependencies or tools

## Error Handling

Common errors and how to handle them:

| Error Code | Description | Resolution |
|------------|-------------|------------|
| ERR_001 | Error description | How to fix |
| ERR_002 | Error description | How to fix |

## Best Practices

- Best practice 1
- Best practice 2
- Best practice 3

## Limitations

- Known limitation 1
- Known limitation 2

## Related Skills

- [Related Skill 1](./related-skill-1.md)
- [Related Skill 2](./related-skill-2.md)

## Changelog

### Version 1.0.0 (YYYY-MM-DD)
- Initial release

## References

- [External reference 1](https://example.com)
- [External reference 2](https://example.com)
```

## Guidelines

### Naming Conventions

1. **File Names**: Use lowercase with hyphens (e.g., `data-processing-skill.md`)
2. **Skill IDs**: Use namespace prefixes (e.g., `veriloga.data.process`)
3. **Categories**: Use predefined categories to maintain consistency

### Documentation Standards

1. **Clarity**: Write clear, concise descriptions
2. **Examples**: Always include working examples
3. **Completeness**: Document all parameters and outputs
4. **Accuracy**: Keep documentation in sync with implementation
5. **Versioning**: Use semantic versioning (MAJOR.MINOR.PATCH)

### Categories

Standard skill categories:

- `data-processing`: Data transformation and manipulation
- `code-generation`: Code creation and modification
- `analysis`: Analysis and evaluation tasks
- `integration`: Third-party integrations
- `utility`: Helper and utility functions
- `communication`: Communication and notification skills

## Example Skills

### Example: Data Validation Skill

```markdown
# Data Validation Skill

## Metadata
- **Skill ID**: `veriloga.data.validate`
- **Version**: `1.0.0`
- **Category**: `data-processing`
- **Last Updated**: `2026-02-09`
- **Status**: `active`

## Description

Validates input data against predefined schemas and rules. This skill ensures data integrity and compliance with specified formats before processing.

## Capabilities

- Schema validation using JSON Schema
- Type checking and coercion
- Custom validation rules
- Detailed error reporting
- Batch validation support

## Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| data | object/array | Yes | - | Data to validate |
| schema | object | Yes | - | JSON Schema for validation |
| strict | boolean | No | true | Enable strict mode |
| coerce | boolean | No | false | Attempt type coercion |

## Output Format

```json
{
  "valid": true,
  "errors": [],
  "metadata": {
    "timestamp": "2026-02-09T03:44:31Z",
    "itemsValidated": 1
  }
}
```

## Usage Examples

### Example 1: Validate User Data

**Input:**
```json
{
  "data": {
    "name": "John Doe",
    "email": "john@example.com",
    "age": 30
  },
  "schema": {
    "type": "object",
    "properties": {
      "name": {"type": "string"},
      "email": {"type": "string", "format": "email"},
      "age": {"type": "number", "minimum": 0}
    },
    "required": ["name", "email"]
  }
}
```

**Output:**
```json
{
  "valid": true,
  "errors": [],
  "metadata": {
    "timestamp": "2026-02-09T03:44:31Z",
    "itemsValidated": 1
  }
}
```

## Prerequisites

- JSON Schema knowledge
- Understanding of data types

## Error Handling

| Error Code | Description | Resolution |
|------------|-------------|------------|
| VAL_001 | Invalid schema format | Check schema syntax |
| VAL_002 | Data type mismatch | Ensure data matches schema types |
| VAL_003 | Missing required field | Add missing fields to data |

## Best Practices

- Define comprehensive schemas
- Use appropriate validation modes
- Handle validation errors gracefully
- Log validation failures for debugging

## Limitations

- Maximum data size: 10MB
- Complex regex patterns may impact performance
- Custom validators not supported in current version

## Related Skills

- [Data Transformation Skill](./data-transformation.md)
- [Schema Generation Skill](./schema-generation.md)

## Changelog

### Version 1.0.0 (2026-02-09)
- Initial release
- Basic validation features
- JSON Schema support

## References

- [JSON Schema Specification](https://json-schema.org/)
- [Data Validation Best Practices](https://example.com/validation)
```

## Contributing

When adding new skills to this repository:

1. Create a new markdown file following the template above
2. Ensure all required sections are completed
3. Add working examples that can be tested
4. Update the main README.md with links to new skills
5. Tag the skill with appropriate version
6. Submit for review

## Maintenance

- Review skills quarterly for accuracy
- Update deprecated features
- Add new examples as use cases emerge
- Maintain backward compatibility when possible
- Document breaking changes clearly

---

**Note**: This format is designed to be flexible yet comprehensive. Adapt sections as needed for specific skill types while maintaining consistency across the repository.
