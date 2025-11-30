import { useEffect, useRef, useState } from "react";
import * as pdfjsLib from "pdfjs-dist";

// Use unpkg CDN for worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjsLib.version}/build/pdf.worker.min.mjs`;

interface PdfViewerPageProps {
  pdfUrl?: string;
}

function PdfViewerPage({ pdfUrl }: PdfViewerPageProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [numPages, setNumPages] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [scale, setScale] = useState(1.2);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const pdfDocRef = useRef<pdfjsLib.PDFDocumentProxy | null>(null);

  // Get PDF URL from query params if not provided as prop
  const url = pdfUrl || new URLSearchParams(window.location.search).get("url") || "";

  useEffect(() => {
    if (!url) {
      setError("לא סופק קישור ל-PDF");
      setLoading(false);
      return;
    }

    let cancelled = false;

    const loadPdf = async () => {
      try {
        setLoading(true);
        setError(null);

        const loadingTask = pdfjsLib.getDocument(url);
        const pdf = await loadingTask.promise;

        if (cancelled) return;

        pdfDocRef.current = pdf;
        setNumPages(pdf.numPages);
        setLoading(false);
      } catch (err) {
        if (cancelled) return;
        console.error("Error loading PDF:", err);
        setError("שגיאה בטעינת ה-PDF");
        setLoading(false);
      }
    };

    loadPdf();

    return () => {
      cancelled = true;
    };
  }, [url]);

  useEffect(() => {
    if (!pdfDocRef.current || !containerRef.current) return;

    let cancelled = false;

    const renderPage = async () => {
      const pdf = pdfDocRef.current;
      if (!pdf) return;

      try {
        const page = await pdf.getPage(currentPage);
        if (cancelled) return;

        const viewport = page.getViewport({ scale });

        // Clear container
        const container = containerRef.current;
        if (!container) return;
        container.innerHTML = "";

        // Create canvas
        const canvas = document.createElement("canvas");
        const context = canvas.getContext("2d");
        if (!context) return;

        canvas.height = viewport.height;
        canvas.width = viewport.width;
        canvas.style.display = "block";
        canvas.style.margin = "0 auto";

        container.appendChild(canvas);

        await page.render({
          canvasContext: context,
          viewport: viewport,
          canvas: canvas,
        }).promise;
      } catch (err) {
        console.error("Error rendering page:", err);
      }
    };

    renderPage();

    return () => {
      cancelled = true;
    };
  }, [currentPage, scale, numPages]);

  const handlePrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  const handleNextPage = () => {
    if (currentPage < numPages) {
      setCurrentPage(currentPage + 1);
    }
  };

  const handleZoomIn = () => {
    setScale((prev) => Math.min(prev + 0.2, 3));
  };

  const handleZoomOut = () => {
    setScale((prev) => Math.max(prev - 0.2, 0.5));
  };

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loading}>טוען PDF...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.container}>
        <div style={styles.error}>{error}</div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.toolbar}>
        <button onClick={handlePrevPage} disabled={currentPage <= 1} style={styles.button}>
          ◀ הקודם
        </button>
        <span style={styles.pageInfo}>
          עמוד {currentPage} מתוך {numPages}
        </span>
        <button onClick={handleNextPage} disabled={currentPage >= numPages} style={styles.button}>
          הבא ▶
        </button>
        <span style={styles.separator}>|</span>
        <button onClick={handleZoomOut} style={styles.button}>
          −
        </button>
        <span style={styles.zoomInfo}>{Math.round(scale * 100)}%</span>
        <button onClick={handleZoomIn} style={styles.button}>
          +
        </button>
      </div>
      <div ref={containerRef} style={styles.viewer} />
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    backgroundColor: "#525659",
  },
  toolbar: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "12px",
    padding: "10px 20px",
    backgroundColor: "#323639",
    color: "#fff",
    flexShrink: 0,
  },
  button: {
    padding: "6px 12px",
    backgroundColor: "#4a4d50",
    color: "#fff",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
    fontSize: "14px",
  },
  pageInfo: {
    fontSize: "14px",
    minWidth: "120px",
    textAlign: "center",
  },
  zoomInfo: {
    fontSize: "14px",
    minWidth: "50px",
    textAlign: "center",
  },
  separator: {
    color: "#666",
  },
  viewer: {
    flex: 1,
    overflow: "auto",
    padding: "20px",
  },
  loading: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    height: "100%",
    color: "#fff",
    fontSize: "18px",
  },
  error: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    height: "100%",
    color: "#ff6b6b",
    fontSize: "18px",
  },
};

export default PdfViewerPage;
