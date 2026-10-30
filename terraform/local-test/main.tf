
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    multipass = {
      source  = "todoroff/multipass"
      version = "2.1.0"
    }
  }
}

provider "multipass" {
  multipass_path  = "/usr/local/bin/multipass"
  command_timeout = 600
  default_image   = "24.04"
}

variable "request_id" {
  type = string
}

variable "vm_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "site" {
  type = string
}

variable "prefix" {
  type = string
}

variable "prefix_id" {
  type = number
}

variable "ip_candidate" {
  type = string
}

variable "ip_candidate_reserved" {
  type = bool
}

variable "registered_ips_in_prefix" {
  type = number
}

resource "terraform_data" "vm_request" {
  input = {
    request_id               = var.request_id
    vm_name                  = var.vm_name
    environment              = var.environment
    site                     = var.site
    prefix                   = var.prefix
    prefix_id                = var.prefix_id
    ip_address               = var.ip_candidate
    ip_candidate_reserved    = var.ip_candidate_reserved
    registered_ips_in_prefix = var.registered_ips_in_prefix
  }
}

output "vm_request_preview" {
  description = "Vista previa de la solicitud obtenida de NetBox"
  value       = terraform_data.vm_request.output
}
