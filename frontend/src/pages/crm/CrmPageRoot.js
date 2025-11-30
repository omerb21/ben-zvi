"use strict";
var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
Object.defineProperty(exports, "__esModule", { value: true });
var react_1 = require("react");
var crmApi_1 = require("../../api/crmApi");
require("../../styles/crm.css");
var CrmPageLayout_1 = require("./CrmPageLayout");
var crmCharts_1 = require("./crmCharts");
var crmClients_1 = require("./crmClients");
var crmSnapshotsAndExport_1 = require("./crmSnapshotsAndExport");
var crmNotesAndReminders_1 = require("./crmNotesAndReminders");
var crmAdminActions_1 = require("./crmAdminActions");
function CrmPageRoot(_a) {
    var onOpenJustification = _a.onOpenJustification;
    var _b = (0, react_1.useState)([]), clients = _b[0], setClients = _b[1];
    var _c = (0, react_1.useState)(null), selectedClient = _c[0], setSelectedClient = _c[1];
    var _d = (0, react_1.useState)([]), snapshots = _d[0], setSnapshots = _d[1];
    var _e = (0, react_1.useState)(null), selectedSnapshot = _e[0], setSelectedSnapshot = _e[1];
    var _f = (0, react_1.useState)([]), clientHistory = _f[0], setClientHistory = _f[1];
    var _g = (0, react_1.useState)([]), fundHistory = _g[0], setFundHistory = _g[1];
    var _h = (0, react_1.useState)([]), notes = _h[0], setNotes = _h[1];
    var _j = (0, react_1.useState)([]), reminders = _j[0], setReminders = _j[1];
    var _k = (0, react_1.useState)(null), summary = _k[0], setSummary = _k[1];
    var _l = (0, react_1.useState)([]), monthlyChange = _l[0], setMonthlyChange = _l[1];
    var _m = (0, react_1.useState)({}), clientDetailsMap = _m[0], setClientDetailsMap = _m[1];
    var _o = (0, react_1.useState)(""), clientFilter = _o[0], setClientFilter = _o[1];
    var _p = (0, react_1.useState)(""), newClientIdNumber = _p[0], setNewClientIdNumber = _p[1];
    var _q = (0, react_1.useState)(""), newClientFullName = _q[0], setNewClientFullName = _q[1];
    var _r = (0, react_1.useState)(""), newClientEmail = _r[0], setNewClientEmail = _r[1];
    var _s = (0, react_1.useState)(""), newClientPhone = _s[0], setNewClientPhone = _s[1];
    var _t = (0, react_1.useState)(""), newClientBirthDate = _t[0], setNewClientBirthDate = _t[1];
    var _u = (0, react_1.useState)(""), newClientGender = _u[0], setNewClientGender = _u[1];
    var _v = (0, react_1.useState)(""), newClientMaritalStatus = _v[0], setNewClientMaritalStatus = _v[1];
    var _w = (0, react_1.useState)(""), newClientEmployerName = _w[0], setNewClientEmployerName = _w[1];
    var _x = (0, react_1.useState)(""), newClientEmployerHp = _x[0], setNewClientEmployerHp = _x[1];
    var _y = (0, react_1.useState)(""), newClientEmployerAddress = _y[0], setNewClientEmployerAddress = _y[1];
    var _z = (0, react_1.useState)(""), newClientEmployerPhone = _z[0], setNewClientEmployerPhone = _z[1];
    var _0 = (0, react_1.useState)(""), editFirstName = _0[0], setEditFirstName = _0[1];
    var _1 = (0, react_1.useState)(""), editLastName = _1[0], setEditLastName = _1[1];
    var _2 = (0, react_1.useState)(""), editEmail = _2[0], setEditEmail = _2[1];
    var _3 = (0, react_1.useState)(""), editPhone = _3[0], setEditPhone = _3[1];
    var _4 = (0, react_1.useState)(""), editBirthDate = _4[0], setEditBirthDate = _4[1];
    var _5 = (0, react_1.useState)(""), editAddressStreet = _5[0], setEditAddressStreet = _5[1];
    var _6 = (0, react_1.useState)(""), editAddressCity = _6[0], setEditAddressCity = _6[1];
    var _7 = (0, react_1.useState)(""), editAddressPostalCode = _7[0], setEditAddressPostalCode = _7[1];
    var _8 = (0, react_1.useState)(""), editGender = _8[0], setEditGender = _8[1];
    var _9 = (0, react_1.useState)(""), editMaritalStatus = _9[0], setEditMaritalStatus = _9[1];
    var _10 = (0, react_1.useState)(""), editEmployerName = _10[0], setEditEmployerName = _10[1];
    var _11 = (0, react_1.useState)(""), editEmployerHp = _11[0], setEditEmployerHp = _11[1];
    var _12 = (0, react_1.useState)(""), editEmployerAddress = _12[0], setEditEmployerAddress = _12[1];
    var _13 = (0, react_1.useState)(""), editEmployerPhone = _13[0], setEditEmployerPhone = _13[1];
    var _14 = (0, react_1.useState)([]), beneficiaries = _14[0], setBeneficiaries = _14[1];
    var _15 = (0, react_1.useState)([]), crmImportFiles = _15[0], setCrmImportFiles = _15[1];
    var _16 = (0, react_1.useState)(""), crmImportMonth = _16[0], setCrmImportMonth = _16[1];
    var _17 = (0, react_1.useState)(false), isCrmImporting = _17[0], setIsCrmImporting = _17[1];
    var _18 = (0, react_1.useState)(false), isCrmClearing = _18[0], setIsCrmClearing = _18[1];
    var _19 = (0, react_1.useState)(null), crmAdminMessage = _19[0], setCrmAdminMessage = _19[1];
    var _20 = (0, react_1.useState)(null), crmAdminError = _20[0], setCrmAdminError = _20[1];
    var _21 = (0, react_1.useState)(""), newNoteText = _21[0], setNewNoteText = _21[1];
    var _22 = (0, react_1.useState)(""), newNoteReminder = _22[0], setNewNoteReminder = _22[1];
    var _23 = (0, react_1.useState)(""), newSnapshotFundCode = _23[0], setNewSnapshotFundCode = _23[1];
    var _24 = (0, react_1.useState)(""), newSnapshotFundName = _24[0], setNewSnapshotFundName = _24[1];
    var _25 = (0, react_1.useState)(""), newSnapshotFundType = _25[0], setNewSnapshotFundType = _25[1];
    var _26 = (0, react_1.useState)(""), newSnapshotAmount = _26[0], setNewSnapshotAmount = _26[1];
    var _27 = (0, react_1.useState)(""), newSnapshotDate = _27[0], setNewSnapshotDate = _27[1];
    var _28 = (0, react_1.useState)(false), loading = _28[0], setLoading = _28[1];
    var _29 = (0, react_1.useState)(null), error = _29[0], setError = _29[1];
    var _30 = (0, react_1.useState)("main"), viewMode = _30[0], setViewMode = _30[1];
    var _31 = (0, react_1.useState)(null), selectedMonth = _31[0], setSelectedMonth = _31[1];
    (0, react_1.useEffect)(function () {
        setLoading(true);
        Promise.all([
            (0, crmApi_1.fetchClientSummaries)(),
            (0, crmApi_1.fetchSummary)(),
            (0, crmApi_1.fetchReminders)(),
            (0, crmApi_1.fetchClients)(),
            (0, crmApi_1.fetchMonthlyChange)(),
        ])
            .then(function (_a) {
            var clientSummaries = _a[0], summaryData = _a[1], remindersData = _a[2], clientsData = _a[3], monthlyChangeData = _a[4];
            setClients(clientSummaries);
            setSummary(summaryData);
            setReminders(remindersData);
            setMonthlyChange(monthlyChangeData);
            var detailsMap = {};
            clientsData.forEach(function (client) {
                detailsMap[client.id] = client;
            });
            setClientDetailsMap(detailsMap);
            setError(null);
        })
            .catch(function () {
            setError("שגיאה בטעינת נתוני CRM");
        })
            .finally(function () {
            setLoading(false);
        });
    }, []);
    var reloadForMonth = function (month) {
        if (!month) {
            return;
        }
        setLoading(true);
        Promise.all([(0, crmApi_1.fetchClientSummaries)(month), (0, crmApi_1.fetchSummary)(month)])
            .then(function (_a) {
            var clientSummaries = _a[0], summaryData = _a[1];
            setClients(clientSummaries);
            setSummary(summaryData);
            setSelectedMonth(summaryData.month);
            setError(null);
        })
            .catch(function () {
            setError("שגיאה בטעינת נתוני CRM");
        })
            .finally(function () {
            setLoading(false);
        });
    };
    var handleMonthInputChange = function (value) {
        if (!value) {
            return;
        }
        reloadForMonth(value);
    };
    var handleShiftMonth = function (delta) {
        var baseMonth = (selectedMonth || (summary === null || summary === void 0 ? void 0 : summary.month) || "").slice(0, 7);
        if (!baseMonth) {
            return;
        }
        var parts = baseMonth.split("-");
        if (parts.length !== 2) {
            return;
        }
        var year = parseInt(parts[0], 10);
        var month = parseInt(parts[1], 10);
        if (!Number.isFinite(year) || !Number.isFinite(month)) {
            return;
        }
        month += delta;
        if (month < 1) {
            month = 12;
            year -= 1;
        }
        else if (month > 12) {
            month = 1;
            year += 1;
        }
        var yearStr = year.toString().padStart(4, "0");
        var monthStr = month.toString().padStart(2, "0");
        reloadForMonth("".concat(yearStr, "-").concat(monthStr));
    };
    var effectiveMonth = selectedMonth || (summary === null || summary === void 0 ? void 0 : summary.month) || null;
    var totalClients = clients.length;
    var totalAssetsValue = clients.reduce(function (sum, client) { return sum + (client.totalAmount || 0); }, 0);
    var totalFundsValue = clients.reduce(function (sum, client) { return sum + (client.fundCount || 0); }, 0);
    var sourcesSet = new Set();
    clients.forEach(function (client) {
        if (client.rawSources && client.rawSources !== "אין נתונים") {
            client.rawSources.split(",").forEach(function (source) {
                var trimmed = source.trim();
                if (trimmed) {
                    sourcesSet.add(trimmed);
                }
            });
        }
    });
    var totalSourcesValue = sourcesSet.size;
    var latestSnapshotsByFund = {};
    snapshots.forEach(function (snapshot) {
        var key = snapshot.fundCode;
        var existing = latestSnapshotsByFund[key];
        if (!existing || snapshot.snapshotDate > existing.snapshotDate) {
            latestSnapshotsByFund[key] = snapshot;
        }
    });
    var latestSnapshots = Object.values(latestSnapshotsByFund);
    var _32 = (0, crmCharts_1.buildHistoryChartData)(clientHistory), historyChartPath = _32.path, historyChartPoints = _32.points;
    var _33 = (0, crmCharts_1.buildMonthlyChangeChartData)(monthlyChange), monthlyTrendPath = _33.path, monthlyTrendPoints = _33.points;
    var handleLoadClientDetails = function (client) {
        (0, crmClients_1.loadClientDetailsAction)({
            client: client,
            setSelectedClient: setSelectedClient,
            setViewMode: setViewMode,
            setSnapshots: setSnapshots,
            setSelectedSnapshot: setSelectedSnapshot,
            setClientHistory: setClientHistory,
            setFundHistory: setFundHistory,
            setNotes: setNotes,
            setLoading: setLoading,
            setClientDetailsMap: setClientDetailsMap,
            setEditFirstName: setEditFirstName,
            setEditLastName: setEditLastName,
            setEditEmail: setEditEmail,
            setEditPhone: setEditPhone,
            setEditBirthDate: setEditBirthDate,
            setEditAddressStreet: setEditAddressStreet,
            setEditAddressCity: setEditAddressCity,
            setEditAddressPostalCode: setEditAddressPostalCode,
            setEditGender: setEditGender,
            setEditMaritalStatus: setEditMaritalStatus,
            setEditEmployerName: setEditEmployerName,
            setEditEmployerHp: setEditEmployerHp,
            setEditEmployerAddress: setEditEmployerAddress,
            setEditEmployerPhone: setEditEmployerPhone,
            setError: setError,
            setBeneficiaries: setBeneficiaries,
        });
    };
    var handleCreateClient = function () {
        (0, crmClients_1.createClientAction)({
            newClientIdNumber: newClientIdNumber,
            newClientFullName: newClientFullName,
            newClientEmail: newClientEmail,
            newClientPhone: newClientPhone,
            newClientBirthDate: newClientBirthDate,
            newClientGender: newClientGender,
            newClientMaritalStatus: newClientMaritalStatus,
            newClientEmployerName: newClientEmployerName,
            newClientEmployerHp: newClientEmployerHp,
            newClientEmployerAddress: newClientEmployerAddress,
            newClientEmployerPhone: newClientEmployerPhone,
            setLoading: setLoading,
            setClients: setClients,
            setClientDetailsMap: setClientDetailsMap,
            setNewClientIdNumber: setNewClientIdNumber,
            setNewClientFullName: setNewClientFullName,
            setNewClientEmail: setNewClientEmail,
            setNewClientPhone: setNewClientPhone,
            setNewClientBirthDate: setNewClientBirthDate,
            setNewClientGender: setNewClientGender,
            setNewClientMaritalStatus: setNewClientMaritalStatus,
            setNewClientEmployerName: setNewClientEmployerName,
            setNewClientEmployerHp: setNewClientEmployerHp,
            setNewClientEmployerAddress: setNewClientEmployerAddress,
            setNewClientEmployerPhone: setNewClientEmployerPhone,
            setError: setError,
        });
    };
    var handleSaveClientDetails = function () {
        (0, crmClients_1.saveClientDetailsAction)({
            selectedClient: selectedClient,
            editFirstName: editFirstName,
            editLastName: editLastName,
            editEmail: editEmail,
            editPhone: editPhone,
            editBirthDate: editBirthDate,
            editAddressStreet: editAddressStreet,
            editAddressCity: editAddressCity,
            editAddressPostalCode: editAddressPostalCode,
            editGender: editGender,
            editMaritalStatus: editMaritalStatus,
            editEmployerName: editEmployerName,
            editEmployerHp: editEmployerHp,
            editEmployerAddress: editEmployerAddress,
            editEmployerPhone: editEmployerPhone,
            beneficiaries: beneficiaries,
            setLoading: setLoading,
            setClientDetailsMap: setClientDetailsMap,
            setSelectedClient: setSelectedClient,
            setClients: setClients,
            setError: setError,
        });
    };
    var handleDeleteClient = function () {
        (0, crmClients_1.deleteClientAction)({
            selectedClient: selectedClient,
            setLoading: setLoading,
            setClients: setClients,
            setClientDetailsMap: setClientDetailsMap,
            setSnapshots: setSnapshots,
            setSelectedSnapshot: setSelectedSnapshot,
            setClientHistory: setClientHistory,
            setFundHistory: setFundHistory,
            setNotes: setNotes,
            setReminders: setReminders,
            setSelectedClient: setSelectedClient,
            setViewMode: setViewMode,
            setError: setError,
        });
    };
    var handleSelectSnapshot = function (snapshot) {
        (0, crmSnapshotsAndExport_1.selectSnapshotAction)({
            snapshot: snapshot,
            selectedClient: selectedClient,
            setSelectedSnapshot: setSelectedSnapshot,
            setFundHistory: setFundHistory,
            setLoading: setLoading,
            setError: setError,
        });
    };
    var handleCreateSnapshot = function () {
        (0, crmSnapshotsAndExport_1.createSnapshotAction)({
            selectedClient: selectedClient,
            newSnapshotFundCode: newSnapshotFundCode,
            newSnapshotAmount: newSnapshotAmount,
            newSnapshotDate: newSnapshotDate,
            newSnapshotFundType: newSnapshotFundType,
            newSnapshotFundName: newSnapshotFundName,
            setLoading: setLoading,
            setSnapshots: setSnapshots,
            setNewSnapshotFundCode: setNewSnapshotFundCode,
            setNewSnapshotFundName: setNewSnapshotFundName,
            setNewSnapshotFundType: setNewSnapshotFundType,
            setNewSnapshotAmount: setNewSnapshotAmount,
            setNewSnapshotDate: setNewSnapshotDate,
            setError: setError,
        });
    };
    var handleExportClientReport = function () {
        (0, crmSnapshotsAndExport_1.exportClientReportAction)({
            selectedClient: selectedClient,
            latestSnapshots: latestSnapshots,
        });
    };
    var handleExportClientPdf = function () {
        (0, crmSnapshotsAndExport_1.exportClientPdfAction)({
            selectedClient: selectedClient,
            latestSnapshots: latestSnapshots,
        });
    };
    var handleDismissNote = function (noteId) {
        (0, crmNotesAndReminders_1.dismissNoteAction)({
            selectedClient: selectedClient,
            noteId: noteId,
            setNotes: setNotes,
            setError: setError,
        });
    };
    var handleClearNoteReminder = function (noteId) {
        (0, crmNotesAndReminders_1.clearNoteReminderAction)({
            selectedClient: selectedClient,
            noteId: noteId,
            setNotes: setNotes,
            setError: setError,
        });
    };
    var handleDeleteNote = function (noteId) {
        (0, crmNotesAndReminders_1.deleteNoteAction)({
            selectedClient: selectedClient,
            noteId: noteId,
            setNotes: setNotes,
            setError: setError,
        });
    };
    var handleSubmitNote = function (event) {
        event.preventDefault();
        (0, crmNotesAndReminders_1.submitNoteAction)({
            selectedClient: selectedClient,
            newNoteText: newNoteText,
            newNoteReminder: newNoteReminder,
            setNotes: setNotes,
            setNewNoteText: setNewNoteText,
            setNewNoteReminder: setNewNoteReminder,
            setError: setError,
        });
    };
    var handleReminderGoToClient = function (reminder) {
        var client = clients.find(function (c) { return c.id === reminder.clientId; }) || null;
        if (!client) {
            return;
        }
        handleLoadClientDetails(client);
    };
    var handleDismissReminder = function (reminder) {
        (0, crmNotesAndReminders_1.dismissReminderAction)({
            reminder: reminder,
            setReminders: setReminders,
            setError: setError,
        });
    };
    var handleClearReminderFromGlobal = function (reminder) {
        (0, crmNotesAndReminders_1.clearReminderGlobalAction)({
            reminder: reminder,
            setReminders: setReminders,
            setError: setError,
        });
    };
    var handleCrmFileChange = function (event) {
        (0, crmAdminActions_1.crmFileChangeHandler)({
            event: event,
            setCrmImportFiles: setCrmImportFiles,
        });
    };
    var handleRunCrmImport = function () {
        (0, crmAdminActions_1.runCrmImportAction)({
            crmImportFiles: crmImportFiles,
            crmImportMonth: crmImportMonth,
            isCrmImporting: isCrmImporting,
            isCrmClearing: isCrmClearing,
            setIsCrmImporting: setIsCrmImporting,
            setCrmAdminMessage: setCrmAdminMessage,
            setCrmAdminError: setCrmAdminError,
        });
    };
    var handleClearCrmDataLocal = function () {
        (0, crmAdminActions_1.clearCrmDataLocalAction)({
            isCrmImporting: isCrmImporting,
            isCrmClearing: isCrmClearing,
