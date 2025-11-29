import { useEffect, useRef, useState, type MutableRefObject } from "react";

export type AdobePdfViewerState = {
  pdfPreviewUrl: string | null;
  setPdfPreviewUrl: (value: string | null) => void;
  useAdobeViewer: boolean;
  adobeViewRef: MutableRefObject<any | null>;
};

export function useAdobePdfViewer(): AdobePdfViewerState {
  const [pdfPreviewUrl, setPdfPreviewUrl] = useState<string | null>(null);
  const [useAdobeViewer, setUseAdobeViewer] = useState(false);
  const adobeViewRef = useRef<any | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    const w: any = window;

    const onReady = () => {
      if (w.ADOBE_PDF_EMBED_API_KEY) {
        setUseAdobeViewer(true);
      }
    };

    if (w.AdobeDC) {
      onReady();
      return;
    }

    document.addEventListener("adobe_dc_view_sdk.ready", onReady);
    return () => {
      document.removeEventListener("adobe_dc_view_sdk.ready", onReady);
    };
  }, []);

  useEffect(() => {
    if (!useAdobeViewer || !pdfPreviewUrl) {
      return;
    }
    if (typeof window === "undefined") {
      return;
    }
    const w: any = window;
    if (!w.AdobeDC || !w.ADOBE_PDF_EMBED_API_KEY) {
      return;
    }
    if (pdfPreviewUrl.includes("/advice.html")) {
      return;
    }
    const viewerElement = document.getElementById("adobe-pdf-viewer");
    if (!viewerElement) {
      return;
    }

    const view = new w.AdobeDC.View({
      clientId: w.ADOBE_PDF_EMBED_API_KEY,
      divId: "adobe-pdf-viewer",
    });
    adobeViewRef.current = view;

    view.previewFile(
      {
        content: {
          location: {
            url: pdfPreviewUrl,
          },
        },
        metaData: {
          fileName: "טופס.pdf",
        },
      },
      {
        embedMode: "SIZED_CONTAINER",
        showDownloadPDF: true,
        showPrintPDF: true,
      }
    );
  }, [useAdobeViewer, pdfPreviewUrl]);

  return {
    pdfPreviewUrl,
    setPdfPreviewUrl,
    useAdobeViewer,
    adobeViewRef,
  };
}
