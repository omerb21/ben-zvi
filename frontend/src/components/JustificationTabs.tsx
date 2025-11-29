type JustificationView = "client" | "market" | "forms";

type Props = {
  currentView: JustificationView;
  onChangeView: (view: JustificationView) => void;
};

function JustificationTabs({ currentView, onChangeView }: Props) {
  return (
    <div className="just-tabs">
      <div className="just-tabs-left">
        <button
          type="button"
          className={
            currentView === "market"
              ? "just-tab-button just-tab-button-dashboard just-tab-button-active"
              : "just-tab-button just-tab-button-dashboard"
          }
          onClick={() => onChangeView("market")}
        >
          דשבורד
        </button>
      </div>
      <div className="just-tabs-right">
        <button
          type="button"
          className={
            currentView === "client"
              ? "just-tab-button just-tab-button-active"
              : "just-tab-button"
          }
          onClick={() => onChangeView("client")}
        >
          הנמקה ללקוח
        </button>
        <button
          type="button"
          className={
            currentView === "forms"
              ? "just-tab-button just-tab-button-active"
              : "just-tab-button"
          }
          onClick={() => onChangeView("forms")}
        >
          עריכת טפסים
        </button>
      </div>
    </div>
  );
}

export default JustificationTabs;
