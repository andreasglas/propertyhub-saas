function escapeCsvValue(value: unknown) {
  if (value === null || value === undefined) {
    return "";
  }
  const text = typeof value === "boolean" ? (value ? "True" : "False") : String(value);
  return /[",\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

/** Erzeugt CSV im selben Format wie Pythons `csv.writer` im Backend. */
export function toCsv(rows: unknown[][]) {
  return rows.map((row) => row.map(escapeCsvValue).join(",")).join("\r\n") + "\r\n";
}

function toPdfSafeText(value: string) {
  return value
    .replace(/ä/g, "ae")
    .replace(/ö/g, "oe")
    .replace(/ü/g, "ue")
    .replace(/Ä/g, "Ae")
    .replace(/Ö/g, "Oe")
    .replace(/Ü/g, "Ue")
    .replace(/ß/g, "ss")
    .replace(/€/g, "EUR")
    .replace(/[–—]/g, "-")
    .replace(/·/g, "|")
    .replace(/[^\x20-\x7e]/g, "?")
    .replace(/([\\()])/g, "\\$1");
}

/**
 * Erzeugt ein einfaches, gültiges einseitiges PDF ohne externe Bibliotheken.
 * `toPdfSafeText` stellt reines ASCII sicher, daher entsprechen String-Längen den Byte-Offsets.
 */
export function createSimplePdf(lines: string[]) {
  const maxLines = 48;
  const visibleLines =
    lines.length > maxLines ? [...lines.slice(0, maxLines - 1), "... (gekuerzt)"] : lines;
  const textCommands = visibleLines
    .map((line, index) => `${index === 0 ? "" : "0 -16 Td "}(${toPdfSafeText(line)}) Tj`)
    .join("\n");
  const content = `BT\n/F1 10 Tf\n50 800 Td\n${textCommands}\nET`;
  const objects = [
    "<< /Type /Catalog /Pages 2 0 R >>",
    "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
    "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
    `<< /Length ${content.length} >>\nstream\n${content}\nendstream`,
    "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
  ];
  let output = "%PDF-1.4\n";
  const offsets: number[] = [];
  objects.forEach((body, index) => {
    offsets.push(output.length);
    output += `${index + 1} 0 obj\n${body}\nendobj\n`;
  });
  const xrefOffset = output.length;
  output += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
  output += offsets.map((offset) => `${String(offset).padStart(10, "0")} 00000 n \n`).join("");
  output += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF\n`;
  return output;
}
