(function () {
  function setupSignaturePad() {
    var canvas = document.getElementById("signature-canvas");
    var clearBtn = document.getElementById("clear-signature");
    var pasteBtn = document.getElementById("paste-signature");
    var submitBtn = document.getElementById("submit-signature");
    var statusEl = document.getElementById("status-message");
    var signedLink = document.getElementById("signed-packet-link");
    var sectionEl = document.querySelector(".signature-section");
    var openPacketRow = document.querySelector(".open-packet-link");

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

    // פונקציה לציור תמונה על הקנבס
    function drawImageOnCanvas(img) {
      var rect = canvas.getBoundingClientRect();
      var canvasWidth = rect.width;
      var canvasHeight = rect.height;

      // חישוב יחס גודל כדי להתאים את התמונה לקנבס
      var imgRatio = img.width / img.height;
      var canvasRatio = canvasWidth / canvasHeight;

      var drawWidth, drawHeight, offsetX, offsetY;

      if (imgRatio > canvasRatio) {
        // התמונה רחבה יותר יחסית - התאם לרוחב
        drawWidth = canvasWidth * 0.9;
        drawHeight = drawWidth / imgRatio;
      } else {
        // התמונה גבוהה יותר יחסית - התאם לגובה
        drawHeight = canvasHeight * 0.9;
        drawWidth = drawHeight * imgRatio;
      }

      // מרכז את התמונה
      offsetX = (canvasWidth - drawWidth) / 2;
      offsetY = (canvasHeight - drawHeight) / 2;

      // נקה את הקנבס וצייר את התמונה
      ctx.clearRect(0, 0, canvasWidth, canvasHeight);
      ctx.fillStyle = "#fafafa";
      ctx.fillRect(0, 0, canvasWidth, canvasHeight);
      ctx.drawImage(img, offsetX, offsetY, drawWidth, drawHeight);

      hasDrawn = true;
      statusEl.textContent = "התמונה הודבקה בהצלחה";
      statusEl.className = "status-message status-success";
    }

    // פונקציה לטיפול בהדבקה מהקליפבורד
    function handlePasteFromClipboard() {
      if (!navigator.clipboard || !navigator.clipboard.read) {
        statusEl.textContent = "הדפדפן לא תומך בהדבקה מהקליפבורד";
        statusEl.className = "status-message status-error";
        return;
      }

      navigator.clipboard.read().then(function (items) {
        for (var i = 0; i < items.length; i++) {
          var item = items[i];
          var imageType = item.types.find(function (type) {
            return type.startsWith("image/");
          });

          if (imageType) {
            item.getType(imageType).then(function (blob) {
              var img = new Image();
              img.onload = function () {
                drawImageOnCanvas(img);
                URL.revokeObjectURL(img.src);
              };
              img.onerror = function () {
                statusEl.textContent = "שגיאה בטעינת התמונה";
                statusEl.className = "status-message status-error";
                URL.revokeObjectURL(img.src);
              };
              img.src = URL.createObjectURL(blob);
            }).catch(function () {
              statusEl.textContent = "שגיאה בקריאת התמונה מהקליפבורד";
              statusEl.className = "status-message status-error";
            });
            return;
          }
        }
        statusEl.textContent = "לא נמצאה תמונה בקליפבורד";
        statusEl.className = "status-message status-error";
      }).catch(function (err) {
        // אם אין הרשאה, ננסה דרך paste event
        statusEl.textContent = "נא להעתיק תמונה ללוח (Ctrl+C) ואז ללחוץ שוב";
        statusEl.className = "status-message status-error";
      });
    }

    // כפתור הדבקה
    if (pasteBtn) {
      pasteBtn.addEventListener("click", handlePasteFromClipboard);
    }

    // תמיכה בהדבקה ישירה עם Ctrl+V על הקנבס או הדף
    document.addEventListener("paste", function (e) {
      var items = e.clipboardData && e.clipboardData.items;
      if (!items) return;

      for (var i = 0; i < items.length; i++) {
        if (items[i].type.indexOf("image") !== -1) {
          e.preventDefault();
          var blob = items[i].getAsFile();
          if (blob) {
            var img = new Image();
            img.onload = function () {
              drawImageOnCanvas(img);
              URL.revokeObjectURL(img.src);
            };
            img.onerror = function () {
              statusEl.textContent = "שגיאה בטעינת התמונה";
              statusEl.className = "status-message status-error";
              URL.revokeObjectURL(img.src);
            };
            img.src = URL.createObjectURL(blob);
          }
          return;
        }
      }
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
            statusEl.textContent = "החתימה התקבלה בהצלחה.";
            statusEl.className = "status-message status-success";

            if (signedLink) {
              // ודא שהקישור מצביע ל-PDF החתום גם אם ה-HTML הישן בקאש.
              var linkEl = signedLink.querySelector("a");
              if (
                linkEl &&
                window.SIGNING_CONFIG &&
                window.SIGNING_CONFIG.signedPacketUrl
              ) {
                linkEl.href = window.SIGNING_CONFIG.signedPacketUrl;
              }

              signedLink.className = "signed-packet-link visible";
            }

            if (sectionEl && !sectionEl.classList.contains("completed")) {
              sectionEl.classList.add("completed");
            }

            if (openPacketRow) {
              openPacketRow.style.display = "none";
            }
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
