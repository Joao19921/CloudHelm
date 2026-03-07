# Terraform V1 (Modular)

This folder contains modular Terraform stubs generated for educational and bootstrap purposes.

## Modules

- `network`
- `compute`
- `database`
- `observability`
- `security`

## Usage

```bash
terraform init
terraform plan -var="provider=aws" -var="project_name=cloudhelm-v1"
```

Change `provider` to `gcp` or `azure` as needed.
