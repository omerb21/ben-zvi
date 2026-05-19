import { useEffect, useState, ChangeEvent } from "react";
import {
  NewProduct,
  buildAdvicePdfUrl,
  buildB1PdfUrl,
  buildKitPdfUrl,
} from "../../api/justificationApi";
import httpClient from "../../api/httpClient";
import type { Client } from "../../api/crmApi";
import "../../styles/justification.css";
import JustificationTabs from "../../components/JustificationTabs";
import JustificationMarketDashboard from "../../components/JustificationMarketDashboard";
import JustificationFormsPanel from "../../components/JustificationFormsPanel";
import JustificationClientHeader from "../../components/JustificationClientHeader";
import JustificationExistingProductsSection from "../../components/JustificationExistingProductsSectionRoot";
import JustificationNewProductsSection from "../../components/JustificationNewProductsSection";
import { useJustificationPdfAndPackets } from "../../components/justification/useJustificationPdfAndPackets";
import { useAdobePdfViewer } from "../../components/justification/useAdobePdfViewer";
import { useJustificationGemel } from "../../components/justification/useJustificationGemel";
import { useJustificationClients } from "./useJustificationClients";
import { useJustificationProducts } from "./useJustificationProducts";

export type Props = {
  savingProductsReloadKey?: number;
  initialClientId?: number | null;
  onGemelNetImportCompleted?: () => void;
};

function JustificationPageRoot({
  savingProductsReloadKey = 0,
  initialClientId = null,
  onGemelNetImportCompleted,
}: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"client" | "market" | "forms">("client");

  const {
    gemelFile,
    isGemelImporting,
    isJustificationClearing,
    isDeletingDocuments,
    importStatus,
    importError,
    handleGemelFileChange,
    handleRunGemelImport,
    handleClearJustificationData,
    handleDeleteAllDocuments,
  } = useJustificationGemel(onGemelNetImportCompleted);

  const {
    clients,
    selectedClient,
    clientFilter,
    existingProducts,
    crmSnapshots,
    newProducts,
    formInstances,
    selectedExistingProduct,
    selectedNewProduct,
    selectedClientDetails,
    existingFormMode,
    setSelectedClient,
    setClientFilter,
    setExistingProducts,
    setCrmSnapshots,
    setNewProducts,
    setFormInstances,
    setSelectedExistingProduct,
    setSelectedNewProduct,
    setSelectedClientDetails,
    setExistingFormMode,
    handleSyncFromCrm,
  } = useJustificationClients({
    initialClientId,
    setLoading,
    setError,
  });

  const {
    pdfGenerationMessage,
    pdfGenerationIsError,
    packetSignLink,
    packetSignError,
    isPacketSignLoading,
    packetTrimInput,
    packetTrimStatus,
    packetTrimIsError,
    packetUploadFile,
    packetUploadStatus,
    packetUploadIsError,
    clientExportsStatus,
    clientExportsIsError,
    isDeletingClientExports,
    handleOpenAdviceHtml,
    handleDownloadB1Pdf,
    handleGenerateAllKits,
    handleDownloadKitPdf,
    handleGeneratePacketPdf,
    handlePreviewPacketPdf,
    handlePreviewSignedPacketPdf,
    handleCreatePacketSignLink,
    handleTrimPacketPages,
    handlePacketUploadFileChange,
    handleUploadPacketPdf,
    handleDeleteClientExports,
    setPacketTrimInput,
  } = useJustificationPdfAndPackets(selectedClient, newProducts);

  const {
    savingProducts,
    selectedSavingProduct,
    newFormTemplate,
    selectedFundTypeFilter,
    savingProductSearch,
    replacementExistingId,
    createMode,
    newExistingFundType,
    newExistingCompanyName,
    newExistingFundName,
    newExistingFundCode,
    newExistingPersonalNumber,
    newExistingAccumulatedAmount,
    newExistingManagementFeeBalance,
    newExistingManagementFeeContributions,
    newExistingEmploymentStatus,
    newExistingHasRegularContributions,
    editExistingFundType,
    editExistingCompanyName,
    editExistingFundName,
    editExistingFundCode,
    editExistingPersonalNumber,
    editExistingAccumulatedAmount,
    editExistingManagementFeeBalance,
    editExistingManagementFeeContributions,
    editExistingEmploymentStatus,
    editExistingHasRegularContributions,
    replacementLockFundType,
    sortedNewProducts,
    findExistingForNew,
    findMatchingSavingProductForExisting,
    handleCreateExistingProduct,
    handleCreateNewProduct,
    handleUpdateExistingProduct,
    handleDeleteExistingProduct,
    handleSelectNewProduct,
    handleCreateFormInstance,
    handleDeleteNewProduct,
    handleDeleteFormInstance,
    setSelectedSavingProduct,
    setNewFormTemplate,
    setSelectedFundTypeFilter,
    setSavingProductSearch,
    setReplacementExistingId,
    setCreateMode,
    setNewExistingFundType,
    setNewExistingCompanyName,
    setNewExistingFundName,
    setNewExistingFundCode,
    setNewExistingPersonalNumber,
    setNewExistingAccumulatedAmount,
    setNewExistingManagementFeeBalance,
    setNewExistingManagementFeeContributions,
    setNewExistingEmploymentStatus,
    setNewExistingHasRegularContributions,
    setEditExistingFundType,
    setEditExistingCompanyName,
    setEditExistingFundName,
    setEditExistingFundCode,
    setEditExistingPersonalNumber,
    setEditExistingAccumulatedAmount,
    setEditExistingManagementFeeBalance,
    setEditExistingManagementFeeContributions,
    setEditExistingEmploymentStatus,
    setEditExistingHasRegularContributions,
  } = useJustificationProducts({
    savingProductsReloadKey,
    selectedClient,
    existingProducts,
    newProducts,
    selectedExistingProduct,
    selectedNewProduct,
    existingFormMode,
    setExistingProducts,
    setNewProducts,
    setFormInstances,
    setSelectedExistingProduct,
    setSelectedNewProduct,
    setLoading,
    setError,
  });

  useAdobePdfViewer();

  const openPdfFromApiUrl = async (url: string) => {
    const response = await httpClient.get<Blob>(url, {
      responseType: "blob",
      validateStatus: () => true,
    });

    if (response.status < 200 || response.status >= 300) {
      return;
    }

    const objectUrl = URL.createObjectURL(response.data);
    window.open(objectUrl, "_blank");
    setTimeout(() => URL.revokeObjectURL(objectUrl), 10000);
  };

  const handlePreviewAdvicePdf = () => {
    if (!selectedClient) {
      return;
    }
    const url = buildAdvicePdfUrl(selectedClient.id);
    void openPdfFromApiUrl(url);
  };

  const handlePreviewB1Pdf = () => {
    if (!selectedClient) {
      return;
    }
    const url = buildB1PdfUrl(selectedClient.id);
    void openPdfFromApiUrl(url);
  };

  const handlePreviewKitPdf = (product: NewProduct) => {
    if (!selectedClient) {
      return;
    }
    const url = buildKitPdfUrl(selectedClient.id, product.id);
    void openPdfFromApiUrl(url);
  };

  if (viewMode === "market") {
    return (
      <div className="justification-page-wrapper">
        <JustificationTabs currentView={viewMode} onChangeView={setViewMode} />
        <div className="justification-page">
          <JustificationMarketDashboard
            savingProducts={savingProducts}
            selectedSavingProduct={selectedSavingProduct}
            onSelectSavingProduct={setSelectedSavingProduct}
            importStatus={importStatus}
            importError={importError}
            loading={loading}
            error={error}
            gemelFile={gemelFile}
            isGemelImporting={isGemelImporting}
            isJustificationClearing={isJustificationClearing}
            isDeletingDocuments={isDeletingDocuments}
            onGemelFileChange={handleGemelFileChange}
            onRunGemelImport={handleRunGemelImport}
            onClearJustificationData={handleClearJustificationData}
            onDeleteAllDocuments={handleDeleteAllDocuments}
          />
        </div>
      </div>
    );
  }

  if (viewMode === "forms") {
    return (
      <div className="justification-page-wrapper">
        <JustificationTabs currentView={viewMode} onChangeView={setViewMode} />
        <div className="justification-page">
          <section className="just-panel just-middle">
            <h2 className="panel-title">
              עריכת טפסי PDF ללקוח
              {selectedClient ? ` - ${selectedClient.fullName}` : ""}
            </h2>
            {!selectedClient && (
              <div className="status-text">
                בחר לקוח בלשונית "הנמקה ללקוח" כדי להציג ולערוך טפסים
              </div>
            )}
            {selectedClient && (
              <JustificationFormsPanel
                selectedClient={selectedClient}
                isPacketSignLoading={isPacketSignLoading}
                isDeletingClientExports={isDeletingClientExports}
                packetTrimInput={packetTrimInput}
                packetUploadFile={packetUploadFile}
                pdfGenerationMessage={pdfGenerationMessage}
                pdfGenerationIsError={pdfGenerationIsError}
                packetSignLink={packetSignLink}
                packetSignError={packetSignError}
                packetTrimStatus={packetTrimStatus}
                packetTrimIsError={packetTrimIsError}
                packetUploadStatus={packetUploadStatus}
                packetUploadIsError={packetUploadIsError}
                clientExportsStatus={clientExportsStatus}
                clientExportsIsError={clientExportsIsError}
                onGeneratePacketPdf={handleGeneratePacketPdf}
                onPreviewPacketPdf={handlePreviewPacketPdf}
                onCreatePacketSignLink={handleCreatePacketSignLink}
                onPreviewSignedPacketPdf={handlePreviewSignedPacketPdf}
                onPacketTrimInputChange={setPacketTrimInput}
                onTrimPacketPages={handleTrimPacketPages}
                onPacketUploadFileChange={handlePacketUploadFileChange}
                onUploadPacketPdf={handleUploadPacketPdf}
                onDeleteClientExports={handleDeleteClientExports}
              />
            )}
          </section>
        </div>
      </div>
    );
  }

  return (
    <div className="justification-page-wrapper">
      <JustificationTabs currentView={viewMode} onChangeView={setViewMode} />
      <div className="justification-page">
        <section className="just-panel just-middle">
          <h2 className="panel-title">
            תהליך הנמקה ללקוח
            {selectedClient ? ` - ${selectedClient.fullName}` : ""}
          </h2>
          <JustificationClientHeader
            clients={clients}
            selectedClientId={selectedClient ? selectedClient.id : null}
            clientFilter={clientFilter}
            selectedClientDetails={selectedClientDetails}
            onClientFilterChange={setClientFilter}
            onClientChange={(clientId) => {
              if (clientId == null) {
                setSelectedClient(null);
                return;
              }
              const client = clients.find((c) => c.id === clientId) || null;
              setSelectedClient(client);
            }}
          />
          {selectedClient && (
            <div className="just-report-actions">
              <button
                type="button"
                className="just-report-button"
                onClick={handleOpenAdviceHtml}
              >
               הפקת מסמך הנמקה
              </button>
              <button
                type="button"
                className="just-report-button"
                onClick={handleDownloadB1Pdf}
              >
               הפקת טופס ב1
              </button>
              <button
                type="button"
                className="just-report-button"
                onClick={handleGenerateAllKits}
              >
                הפקת כל קיטי ההצטרפות
              </button>
            </div>
          )}
          {pdfGenerationMessage && (
            <div
              className={
                pdfGenerationIsError ? "status-text status-error" : "status-text"
              }
            >
              {pdfGenerationMessage}
            </div>
          )}
          <JustificationExistingProductsSection
            existingProducts={existingProducts}
            crmSnapshots={crmSnapshots}
            selectedExistingProduct={selectedExistingProduct}
            loading={loading}
            selectedClient={selectedClient}
            onSyncFromCrm={handleSyncFromCrm}
            existingFormMode={existingFormMode}
            createMode={createMode}
            replacementExistingId={replacementExistingId}
            savingProducts={savingProducts}
            selectedFundTypeFilter={selectedFundTypeFilter}
            savingProductSearch={savingProductSearch}
            selectedSavingProduct={selectedSavingProduct}
            newExistingPersonalNumber={newExistingPersonalNumber}
            newExistingAccumulatedAmount={newExistingAccumulatedAmount}
            newExistingManagementFeeBalance={newExistingManagementFeeBalance}
            newExistingManagementFeeContributions={newExistingManagementFeeContributions}
            newExistingEmploymentStatus={newExistingEmploymentStatus}
            newExistingHasRegularContributions={newExistingHasRegularContributions}
            editExistingPersonalNumber={editExistingPersonalNumber}
            editExistingAccumulatedAmount={editExistingAccumulatedAmount}
            editExistingManagementFeeBalance={editExistingManagementFeeBalance}
            editExistingManagementFeeContributions={
              editExistingManagementFeeContributions
            }
            editExistingEmploymentStatus={editExistingEmploymentStatus}
            editExistingHasRegularContributions={
              editExistingHasRegularContributions
            }
            replacementLockFundType={replacementLockFundType}
            onSetExistingFormMode={setExistingFormMode}
            onSetReplacementExistingId={setReplacementExistingId}
            onSetSelectedExistingProduct={setSelectedExistingProduct}
            onSetCreateMode={setCreateMode}
            onSetSelectedFundTypeFilter={setSelectedFundTypeFilter}
            onSetSelectedSavingProduct={setSelectedSavingProduct}
            onSetSavingProductSearch={setSavingProductSearch}
            onSetNewExistingPersonalNumber={setNewExistingPersonalNumber}
            onSetNewExistingAccumulatedAmount={setNewExistingAccumulatedAmount}
            onSetNewExistingManagementFeeBalance={
              setNewExistingManagementFeeBalance
            }
            onSetNewExistingManagementFeeContributions={
              setNewExistingManagementFeeContributions
            }
            onSetNewExistingEmploymentStatus={setNewExistingEmploymentStatus}
            onSetNewExistingHasRegularContributions={
              setNewExistingHasRegularContributions
            }
            onSetEditExistingPersonalNumber={setEditExistingPersonalNumber}
            onSetEditExistingAccumulatedAmount={setEditExistingAccumulatedAmount}
            onSetEditExistingManagementFeeBalance={setEditExistingManagementFeeBalance}
            onSetEditExistingManagementFeeContributions={
              setEditExistingManagementFeeContributions
            }
            onSetEditExistingEmploymentStatus={setEditExistingEmploymentStatus}
            onSetEditExistingHasRegularContributions={
              setEditExistingHasRegularContributions
            }
            onCreateExistingProduct={handleCreateExistingProduct}
            onCreateNewProduct={handleCreateNewProduct}
            onUpdateExistingProduct={handleUpdateExistingProduct}
            onDeleteExistingProduct={handleDeleteExistingProduct}
            findMatchingSavingProductForExisting={findMatchingSavingProductForExisting}
          />
          <JustificationNewProductsSection
            sortedNewProducts={sortedNewProducts}
            newProducts={newProducts}
            selectedNewProduct={selectedNewProduct}
            loading={loading}
            selectedClient={selectedClient}
            findExistingForNew={findExistingForNew}
            onSelectNewProduct={handleSelectNewProduct}
            onDownloadKitPdf={handleDownloadKitPdf}
            onDeleteNewProduct={handleDeleteNewProduct}
          />
        </section>
      </div>
    </div>
  );
}

export default JustificationPageRoot;
