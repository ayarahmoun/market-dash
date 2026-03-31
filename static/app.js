// Table sorting
document.addEventListener("DOMContentLoaded", function () {
  var table = document.getElementById("signals-table");
  if (!table) return;

  var headers = table.querySelectorAll("th.sortable");
  var sortState = {};

  headers.forEach(function (header) {
    header.addEventListener("click", function () {
      var sortKey = header.getAttribute("data-sort");
      var isNum = header.classList.contains("num");
      var ascending = sortState[sortKey] !== "asc";
      sortState[sortKey] = ascending ? "asc" : "desc";

      var tbody = table.querySelector("tbody");
      var assetRows = [];
      var detailRows = {};
      var rows = tbody.querySelectorAll("tr");

      rows.forEach(function (row) {
        if (row.classList.contains("asset-row")) {
          assetRows.push(row);
        } else if (row.classList.contains("detail-row")) {
          var ticker = row.id.replace("detail-", "");
          detailRows[ticker] = row;
        }
      });

      var colIdx = Array.from(header.parentElement.children).indexOf(header);

      assetRows.sort(function (a, b) {
        var aVal = a.children[colIdx].textContent.trim();
        var bVal = b.children[colIdx].textContent.trim();

        if (isNum) {
          aVal = parseFloat(aVal.replace(/[$%x,]/g, "")) || 0;
          bVal = parseFloat(bVal.replace(/[$%x,]/g, "")) || 0;
        }

        if (aVal < bVal) return ascending ? -1 : 1;
        if (aVal > bVal) return ascending ? 1 : -1;
        return 0;
      });

      while (tbody.firstChild) {
        tbody.removeChild(tbody.firstChild);
      }

      assetRows.forEach(function (row) {
        tbody.appendChild(row);
        var ticker = row.getAttribute("data-ticker");
        if (detailRows[ticker]) {
          tbody.appendChild(detailRows[ticker]);
        }
      });

      headers.forEach(function (h) {
        h.classList.remove("sort-asc", "sort-desc");
      });
      header.classList.add(ascending ? "sort-asc" : "sort-desc");
    });
  });

  // Row expansion
  var assetRows = table.querySelectorAll(".asset-row");
  assetRows.forEach(function (row) {
    row.style.cursor = "pointer";
    row.addEventListener("click", function (e) {
      if (e.target.closest("a")) return;
      var ticker = row.getAttribute("data-ticker");
      var detailRow = document.getElementById("detail-" + ticker);
      if (detailRow) {
        detailRow.classList.toggle("hidden");
      }
    });
  });
});

// Refresh data
function refreshData() {
  var btn = document.getElementById("refresh-btn");
  btn.textContent = "...";
  btn.disabled = true;

  fetch("/api/refresh", { method: "POST" })
    .then(function (r) {
      return r.json();
    })
    .then(function () {
      window.location.reload();
    })
    .catch(function () {
      btn.textContent = "Error";
      setTimeout(function () {
        btn.textContent = "Refresh";
        btn.disabled = false;
      }, 2000);
    });
}

// Auto-refresh every 5 minutes
setInterval(function () {
  fetch("/api/signals")
    .then(function (r) {
      return r.json();
    })
    .then(function (data) {
      var updated = document.querySelector(".last-updated");
      if (updated && data.last_updated) {
        updated.textContent = data.last_updated;
      }
    })
    .catch(function () {});
}, 300000);
