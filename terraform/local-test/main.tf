
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

variable "vm_name" {
  description = "Nombre de la máquina virtual"
  type        = string
}

variable "cpus" {
  description = "Cantidad de CPU"
  type        = number
  default     = 2
}

variable "memory" {
  description = "Memoria RAM"
  type        = string
  default     = "2G"
}

variable "disk" {
  description = "Tamaño del disco"
  type        = string
  default     = "20G"
}

variable "image" {
  description = "Imagen Ubuntu para Multipass"
  type        = string
  default     = "24.04"
}

resource "multipass_instance" "vm" {
  name   = var.vm_name
  image  = var.image
  cpus   = var.cpus
  memory = var.memory
  disk   = var.disk
}

output "vm_name" {
  value = multipass_instance.vm.name
}

output "vm_state" {
  value = multipass_instance.vm.state
}
