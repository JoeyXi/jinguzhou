{{- define "jinguzhou.name" -}}
{{- .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "jinguzhou.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "jinguzhou.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
