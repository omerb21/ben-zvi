import { ReactNode } from "react";
import { AppView } from "../App";
import httpClient from "../api/httpClient";
import "../styles/layout.css";

type Props = {
  currentView: AppView;
  onChangeView: (view: AppView) => void;
  children: ReactNode;
};

function MainLayout({ currentView, onChangeView, children }: Props) {
  const baseUrl = (httpClient.defaults.baseURL || "").replace(/\/+$/, "");
  const logoUrl = `${baseUrl}/static/logo.png`;

  return (
    <div className="app-root">
      <header className="app-header">
        <div className="app-header-left">
          <img src={logoUrl} alt="Ben Zvi Office logo" className="app-logo" />
          <h1 className="app-title">BEN-ZVI OFFICE</h1>
        </div>
        <div className="app-header-right">
          <nav className="app-nav">
            <button
              className={
                currentView === "crm" ? "nav-button nav-button-active" : "nav-button"
              }
              onClick={() => onChangeView("crm")}
              type="button"
            >
              CRM
            </button>
            <button
              className={
                currentView === "justification"
                  ? "nav-button nav-button-active"
                  : "nav-button"
              }
              onClick={() => onChangeView("justification")}
              type="button"
            >
              הנמקה
            </button>
          </nav>
        </div>
      </header>
      <main className="app-content">{children}</main>
    </div>
  );
}

export default MainLayout;
