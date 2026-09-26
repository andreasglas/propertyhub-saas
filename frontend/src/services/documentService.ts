import { apiClient } from "./apiClient";

export type DocumentRecord = {
  id: string;
  organization_id: string;
  related_model: string;
  related_id: string;
  document_type: string;
  file_name: string;
  storage_path?: string | null;
  ocr_status: string;
  ocr_result?: Record<string, string | number | null> | null;
  ocr_processed_at?: string | null;
};

export async function listDocuments() {
  const response = await apiClient.get<DocumentRecord[]>("/documents/");
  return response.data;
}

export async function uploadDocument(payload: {
  related_model: string;
  related_id: string;
  document_type: string;
  file: File;
}) {
  const formData = new FormData();
  formData.set("related_model", payload.related_model);
  formData.set("related_id", payload.related_id);
  formData.set("document_type", payload.document_type);
  formData.set("file", payload.file);

  const response = await apiClient.post<DocumentRecord>("/documents/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
}

export async function processDocumentOcr(documentId: string) {
  const response = await apiClient.post<{ document: DocumentRecord }>(
    `/documents/${documentId}/process-ocr`,
  );
  return response.data.document;
}

export async function applyDocumentOcrToInvoice(documentId: string) {
  const response = await apiClient.post<{
    document: DocumentRecord;
    invoice: {
      id: string;
      organization_id: string;
      property_id?: string | null;
      vendor_name: string;
      invoice_number?: string | null;
      invoice_date?: string | null;
      gross_amount: number;
      status: string;
    };
  }>(`/documents/${documentId}/apply-ocr-to-invoice`);
  return response.data;
}
