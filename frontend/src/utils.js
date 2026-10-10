export function downloadCsv(filename, headers, rows) {
  const escape = value => '"' + String(value ?? '').replaceAll('"', '""') + '"'
  const content = [headers, ...rows].map(row => row.map(escape).join(',')).join('\r\n')
  const url = URL.createObjectURL(new Blob(['\ufeff' + content], { type: 'text/csv;charset=utf-8' }))
  const link = document.createElement('a'); link.href = url; link.download = filename; link.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
