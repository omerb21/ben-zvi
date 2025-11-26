(function () {
  function setupSignaturePad() {
    var canvas = document.getElementById("signature-canvas");
    var clearBtn = document.getElementById("clear-signature");
    var submitBtn = document.getElementById("submit-signature");
    var statusEl = document.getElementById("status-message");

    if (!canvas || !clearBtn || !submitBtn || !statusEl) {
      return;
    }

    var ctx = canvas.getContext("2d");
    var drawing = false;
    var hasDrawn = false;

    function resizeCanvas() {
      var rect = canvas.getBoundingClientRect();
      var ratio = window.devicePixelRatio || 1;
      canvas.width = rect.width * ratio;
      canvas.height = rect.height * ratio;
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
      ctx.lineWidth = 2;
      ctx.lineCap = "round";
      ctx.strokeStyle = "#000";
      ctx.fillStyle = "#fafafa";
      ctx.fillRect(0, 0, rect.width, rect.height);
    }

    resizeCanvas();
    window.addEventListener("resize", function () {
      resizeCanvas();
      hasDrawn = false;
    });

    function getPos(e) {
      var rect = canvas.getBoundingClientRect();
      if (e.touches && e.touches.length > 0) {
        return {
          x: e.touches[0].clientX - rect.left,
          y: e.touches[0].clientY - rect.top,
        };
      }
      return {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      };
    }

    function startDraw(e) {
      e.preventDefault();
      drawing = true;
      hasDrawn = true;
      var pos = getPos(e);
      ctx.beginPath();
      ctx.moveTo(pos.x, pos.y);
    }

    function moveDraw(e) {
      if (!drawing) return;
      e.preventDefault();
      var pos = getPos(e);
      ctx.lineTo(pos.x, pos.y);
      ctx.stroke();
    }

    function endDraw(e) {
      if (!drawing) return;
      e.preventDefault();
      drawing = false;
    }

    canvas.addEventListener("mousedown", startDraw);
    canvas.addEventListener("mousemove", moveDraw);
    window.addEventListener("mouseup", endDraw);

    canvas.addEventListener("touchstart", startDraw, { passive: false });
    canvas.addEventListener("touchmove", moveDraw, { passive: false });
    window.addEventListener("touchend", endDraw, { passive: false });

    clearBtn.addEventListener("click", function () {
      var rect = canvas.getBoundingClientRect();
      ctx.clearRect(0, 0, rect.width, rect.height);
      ctx.fillStyle = "#fafafa";
      ctx.fillRect(0, 0, rect.width, rect.height);
      hasDrawn = false;
      statusEl.textContent = "";
      statusEl.className = "status-message";
    });

    submitBtn.addEventListener("click", function () {
      if (!window.SIGNING_CONFIG || !window.SIGNING_CONFIG.submitUrl) {
        return;
      }
      if (!hasDrawn) {
        statusEl.textContent = "נא לחתום בתיבה לפני השליחה";
        statusEl.className = "status-message status-error";
        return;
      }

      submitBtn.disabled = true;
      clearBtn.disabled = true;
      statusEl.textContent = "שולח חתימה...";
      statusEl.className = "status-message";

      try {
        var dataUrl = canvas.toDataURL("image/png");
        fetch(window.SIGNING_CONFIG.submitUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ signatureDataUrl: dataUrl }),
        })
          .then(function (res) {
            if (!res.ok) {
              throw new Error("sign-submit-failed");
            }
            return res.json().catch(function () {
              return {};
            });
          })
          .then(function () {
            statusEl.textContent = "החתימה התקבלה בהצלחה. ניתן לסגור את הדפדפן.";
            statusEl.className = "status-message status-success";
          })
          .catch(function () {
            statusEl.textContent = "שגיאה בשליחת החתימה. נסה שוב.";
            statusEl.className = "status-message status-error";
            submitBtn.disabled = false;
            clearBtn.disabled = false;
          });
      } catch (e) {
        statusEl.textContent = "שגיאה בשליחת החתימה.";
        statusEl.className = "status-message status-error";
        submitBtn.disabled = false;
        clearBtn.disabled = false;
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupSignaturePad);
  } else {
    setupSignaturePad();
  }
})();
