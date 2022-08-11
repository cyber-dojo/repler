variable "service_name" {
  type    = string
  default = "repler"
}

variable "env" {
  type = string
}

variable "app_port" {
  type    = number
  default = 4657
}

variable "cpu_limit" {
  type    = number
  default = 20
}

variable "mem_limit" {
  type    = number
  default = 64
}

variable "mem_reservation" {
  type    = number
  default = 32
}

variable "TAGGED_IMAGE" {
  type = string
}

# App variables
variable "app_env_vars" {
  type = map(any)
  default = {
    CYBER_DOJO_USE_CONTAINERD = "true"
    CYBER_DOJO_PROMETHEUS     = "false"
    CYBER_DOJO_REPLER_PORT    = "4657"
  }
}

variable "ecr_replication_targets" {
  type    = list(map(string))
  default = []
}

variable "ecr_replication_origin" {
  type    = string
  default = ""
}
