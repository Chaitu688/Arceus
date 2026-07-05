#!/usr/bin/env python3
import argparse
import io
import json
import logging
import os
import pathlib
import shlex
import subprocess
import time
import zipfile
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from urllib.request import Request, urlopen


HTML_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Arceus</title>
  <style>
    :root {
      --bg: #111315;
      --panel: #1d2127;
      --panel-2: #151920;
      --ink: #f4f7fb;
      --muted: #a4adbb;
      --accent: #3468e8;
      --accent-2: #f59e0b;
      --line: #313848;
      --line-2: #283040;
      --good: #37d266;
      --bad: #ff5c5c;
      --shadow: 0 22px 48px rgba(0, 0, 0, 0.34);
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
      color: var(--ink);
      background: linear-gradient(180deg, #171a1f 0%, var(--bg) 100%);
      min-height: 100vh;
    }

    .wrap {
      max-width: 1520px;
      margin: 0 auto;
      padding: 24px 28px 48px;
    }

    .topbar, .panel {
      background: linear-gradient(180deg, rgba(35,41,53,0.96), rgba(26,31,39,0.96));
      border: 1px solid var(--line);
      border-radius: 18px;
      box-shadow: var(--shadow);
    }

    .topbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 24px;
      padding: 14px 20px;
      margin-bottom: 22px;
      border-radius: 0 0 18px 18px;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 18px;
      font-weight: 700;
      font-size: 1.1rem;
    }

    .brand-mark {
      width: 12px;
      height: 12px;
      border-radius: 3px;
      background: linear-gradient(135deg, #2b59d9, #41d57a);
    }

    .nav-tabs {
      display: flex;
      gap: 10px;
      align-items: center;
    }

    .nav-tab {
      padding: 10px 14px;
      border-radius: 8px;
      color: var(--ink);
      font-weight: 700;
      text-decoration: none;
      font-size: 0.95rem;
    }

    .nav-tab.active {
      background: #3c4d69;
    }

    .panel {
      padding: 18px 20px;
      margin-bottom: 18px;
      border-radius: 14px;
    }

    .page-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      margin-bottom: 12px;
    }

    .title-row {
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }

    h1, h2, p { margin: 0; }
    h1 { font-size: 2.05rem; letter-spacing: -0.04em; }
    h2 { font-size: 1rem; }

    .muted { color: var(--muted); }

    .live-dot {
      width: 11px;
      height: 11px;
      background: var(--good);
      box-shadow: 0 0 12px rgba(55, 210, 102, 0.35);
    }

    .chip {
      display: inline-flex;
      align-items: center;
      padding: 7px 12px;
      border-radius: 999px;
      font-size: 0.85rem;
      font-weight: 700;
      background: rgba(55, 210, 102, 0.14);
      color: #8df0a6;
      border: 1px solid rgba(141, 240, 166, 0.18);
    }

    .chip.offline {
      background: rgba(255, 92, 92, 0.12);
      color: #ff9a9a;
      border-color: rgba(255, 92, 92, 0.18);
    }

    .stats {
      display: grid;
      grid-template-columns: repeat(3, minmax(120px, 1fr));
      gap: 12px;
    }

    .stat {
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 12px 14px;
      background: rgba(9, 12, 16, 0.24);
    }

    .stat b {
      display: block;
      margin-top: 6px;
      font-size: 1.25rem;
    }

    .lead {
      margin-top: 10px;
      color: var(--muted);
      max-width: 880px;
      display: none;
    }

    .connect-card {
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 14px;
      background: rgba(9, 12, 16, 0.2);
      margin-top: 18px;
    }

    label {
      display: block;
      margin-bottom: 6px;
      font-size: 0.92rem;
      color: var(--muted);
    }

    input, button {
      font: inherit;
    }

    input {
      width: 100%;
      padding: 12px 14px;
      border-radius: 12px;
      border: 1px solid #3a4353;
      background: #12161d;
      color: var(--ink);
    }

    .row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }

    button {
      border: 0;
      border-radius: 8px;
      padding: 11px 14px;
      cursor: pointer;
      background: var(--accent);
      color: white;
      font-weight: 700;
    }

    button.alt { background: var(--accent-2); }
    button.ghost {
      background: #232a36;
      border: 1px solid #394253;
      color: var(--ink);
    }

    button:disabled {
      opacity: 0.55;
      cursor: wait;
    }

    .toolbar, .action-row {
      display: flex;
      gap: 4px;
      flex-wrap: nowrap;
      align-items: center;
      justify-content: flex-start;
    }

    .action-row button {
      padding: 4px 7px;
      font-size: 0.64rem;
      line-height: 1.2;
      white-space: nowrap;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border-radius: 8px;
      flex: 0 0 auto;
    }

    .device-table-wrap {
      overflow-x: auto;
      border: 1px solid var(--line-2);
      border-radius: 12px;
      background: #23201d;
    }

    .device-table {
      width: 100%;
      border-collapse: collapse;
      min-width: 1540px;
    }

    .device-table th,
    .device-table td {
      padding: 7px 10px;
      border-bottom: 1px solid #334158;
      text-align: left;
      vertical-align: middle;
      line-height: 1.05;
    }

    .device-table th:nth-child(1),
    .device-table td:nth-child(1) {
      width: 145px;
      min-width: 145px;
    }

    .device-table th:nth-child(2),
    .device-table td:nth-child(2) {
      width: 150px;
      min-width: 150px;
      white-space: nowrap;
    }

    .device-table th:nth-child(3),
    .device-table td:nth-child(3) {
      width: 92px;
      min-width: 92px;
      text-align: center;
    }

    .device-table th:nth-child(4),
    .device-table td:nth-child(4) {
      width: 110px;
      min-width: 110px;
      text-align: center;
    }

    .device-table th:nth-child(5),
    .device-table td:nth-child(5) {
      width: 120px;
      min-width: 120px;
      white-space: nowrap;
    }

    .device-table th:nth-child(6),
    .device-table td:nth-child(6) {
      width: 110px;
      min-width: 110px;
      white-space: nowrap;
    }

    .device-table th:nth-child(7),
    .device-table td:nth-child(7) {
      width: 660px;
      min-width: 660px;
    }

    .device-table th {
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #d8e3f0;
      background: #262220;
    }

    .device-table tbody tr:hover {
      background: rgba(43, 59, 84, 0.35);
    }

    .device-table tbody tr.active {
      background: #202b3c;
    }

    .device-name {
      font-weight: 700;
      white-space: nowrap;
    }

    .device-sub {
      font-size: 0.7rem;
      color: var(--muted);
      margin-top: 1px;
      white-space: nowrap;
    }

    .badge {
      display: inline-block;
      padding: 2px 7px;
      border-radius: 999px;
      font-size: 0.66rem;
      white-space: nowrap;
      background: #20314b;
      color: var(--ink);
    }

    .badge.good {
      background: rgba(55, 210, 102, 0.14);
      color: #8df0a6;
    }

    .badge.bad {
      background: rgba(255, 92, 92, 0.12);
      color: #ff9a9a;
    }

    .badge.square {
      border-radius: 4px;
      padding: 2px 6px;
      min-width: 18px;
      text-align: center;
      font-weight: 700;
    }

    .badge.neutral {
      background: rgba(52, 104, 232, 0.14);
      color: #bcd0ff;
    }


    .status {
      margin-bottom: 12px;
      min-height: 24px;
      font-weight: 600;
    }

    .status.good { color: var(--good); }
    .status.bad { color: var(--bad); }

    .terminal {
      height: 240px;
      padding: 14px;
      border-radius: 16px;
      background: #0f1318;
      color: #d9e0eb;
      font-family: "IBM Plex Mono", "Consolas", monospace;
      white-space: pre-wrap;
      overflow: auto;
      line-height: 1.45;
      border: 1px solid #2e3542;
    }

    .overview-actions {
      display: flex;
      gap: 12px;
      align-items: center;
      flex-wrap: wrap;
    }

    .summary-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 18px;
      margin-bottom: 18px;
    }

    .mini-pill {
      display: inline-flex;
      align-items: center;
      border: 1px solid rgba(55, 210, 102, 0.5);
      border-radius: 8px;
      color: #53ef85;
      padding: 7px 12px;
      font-weight: 700;
      background: rgba(15, 88, 36, 0.2);
      font-size: 0.9rem;
    }

    .modal-backdrop {
      position: fixed;
      inset: 0;
      display: none;
      align-items: center;
      justify-content: center;
      background: rgba(0, 0, 0, 0.55);
      padding: 20px;
    }

    .modal-backdrop.open {
      display: flex;
    }

    .modal {
      width: min(440px, 100%);
      background: linear-gradient(180deg, rgba(35,41,53,0.98), rgba(26,31,39,0.98));
      border: 1px solid var(--line);
      border-radius: 18px;
      box-shadow: var(--shadow);
      padding: 18px 20px;
    }

    select {
      width: 100%;
      padding: 12px 14px;
      border-radius: 12px;
      border: 1px solid #3a4353;
      background: #12161d;
      color: var(--ink);
      font: inherit;
      margin-top: 12px;
    }

    @media (max-width: 980px) {
      .page-head,
      .row,
      .stats,
      .topbar,
      .summary-row {
        display: grid;
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <section class="topbar">
      <div class="brand">
        <div class="brand-mark"></div>
        <div class="nav-tabs">
          <a class="nav-tab active" href="#">Status</a>
          <a class="nav-tab" href="#">Settings</a>
        </div>
      </div>
      <div class="toolbar">
        <span class="muted">admin</span>
        <span>Logout</span>
      </div>
    </section>

    <section class="panel">
      <div class="summary-row">
        <div class="title-row">
          <h1>Device Overview</h1>
          <span class="live-dot"></span>
          <span class="chip" id="overviewState">Waiting</span>
          <span class="muted" id="overviewUpdated">Waiting for status...</span>
        </div>
        <div class="overview-actions">
          <button id="connectBtn">Connect Device</button>
          <button class="ghost" id="refreshBtn">Refresh</button>
        </div>
      </div>

      <div class="connect-card">
        <div class="row">
          <div>
            <label for="host">IP</label>
            <input id="host" placeholder="192.168.0.27">
          </div>
          <div>
            <label for="port">Port</label>
            <input id="port" value="5555">
          </div>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="page-head" style="margin-bottom:14px;">
        <div class="stats">
          <div class="stat"><span class="muted">ADB</span><b id="adbVersion">...</b></div>
          <div class="stat"><span class="muted">Devices</span><b id="deviceCount">0</b></div>
          <div class="stat"><span class="muted">Selected</span><b id="selectedText">none</b></div>
        </div>
      </div>
      <input id="remoteDir" type="hidden" value="/data/adb/cosmog2">
      <div class="device-table-wrap">
        <table class="device-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>IP / Port</th>
              <th>Status</th>
              <th>Control</th>
              <th>PoGo Version</th>
              <th>Memory</th>
              <th>Options</th>
            </tr>
          </thead>
          <tbody id="deviceTableBody"></tbody>
        </table>
      </div>
    </section>

    <section class="panel">
      <div class="status" id="statusLine"></div>
      <div class="terminal" id="logPane"></div>
    </section>
  </div>

  <div class="modal-backdrop" id="versionModal">
    <div class="modal">
      <h2>Select PoGo Version</h2>
      <div class="muted" style="margin-top:8px">Choose the version to download, extract, and install.</div>
      <select id="versionSelect"></select>
      <div class="action-row" style="margin-top:16px">
        <button id="versionConfirmBtn">Update PoGo</button>
        <button type="button" class="ghost" id="versionCancelBtn">Cancel</button>
      </div>
    </div>
  </div>

  <div class="modal-backdrop" id="pushConfigModal">
    <div class="modal">
      <h2>Push Config</h2>
      <div class="muted" style="margin-top:8px">Paste the config.toml content to push to the device.</div>
      <textarea id="pushConfigText" style="width:100%;height:200px;margin-top:12px;padding:12px;border-radius:12px;border:1px solid #3a4353;background:#12161d;color:var(--ink);font:0.82rem/1.5 var(--mono,monospace);resize:vertical;box-sizing:border-box;" placeholder="[cosmog]&#10;key = value"></textarea>
      <div class="action-row" style="margin-top:16px">
        <button id="pushConfigConfirmBtn">Push Config</button>
        <button type="button" class="ghost" id="pushConfigCancelBtn">Cancel</button>
      </div>
    </div>
  </div>

  <script>
    const state = {
      selectedSerial: "",
      devices: [],
      defaults: null,
      versions: [],
      pendingPogoSerial: "",
      pendingPushConfigSerial: "",
    };

    const $ = (id) => document.getElementById(id);

    function setStatus(message, kind="") {
      const el = $("statusLine");
      el.textContent = message || "";
      el.className = "status" + (kind ? " " + kind : "");
    }

    function appendLog(message) {
      if (!message) return;
      const pane = $("logPane");
      pane.textContent = message + "\\n\\n" + pane.textContent;
      pane.scrollTop = 0;
    }

    async function api(path, method="GET", body=null) {
      const options = { method, headers: {} };
      if (body !== null) {
        options.headers["Content-Type"] = "application/json";
        options.body = JSON.stringify(body);
      }
      const res = await fetch(path, options);
      const data = await res.json();
      if (!res.ok || data.ok === false) {
        throw new Error(data.error || ("HTTP " + res.status));
      }
      return data;
    }

    function currentRemoteDir() {
      return $("remoteDir").value.trim();
    }

    function renderDevices() {
      const tableBody = $("deviceTableBody");
      tableBody.innerHTML = "";

      if (!state.devices.length) {
        tableBody.innerHTML = '<tr><td colspan="7" class="muted">No devices found.</td></tr>';
      }

      for (const device of state.devices) {
        const isConnected = device.state === "device";
        const row = document.createElement("tr");
        row.className = device.serial === state.selectedSerial ? "active" : "";

        const actionButtons = [];
        if (!isConnected && device.connection_type === "network") {
          actionButtons.push('<button type="button" class="ghost" data-action="connect">Connect</button>');
        }
        if (isConnected) {
          actionButtons.push('<button type="button" data-action="update-pogo">Update PoGo</button>');
          actionButtons.push('<button type="button" class="ghost" data-action="update-cosmog">Update Cosmog</button>');
          actionButtons.push('<button type="button" class="ghost" data-action="start-cosmog">Start Cosmog</button>');
          actionButtons.push('<button type="button" class="ghost" data-action="stop-cosmog">Stop Cosmog</button>');
          actionButtons.push('<button type="button" class="ghost" data-action="cosmog-log">Cosmog Log</button>');
          actionButtons.push('<button type="button" class="ghost" data-action="restart">Restart</button>');
          actionButtons.push('<button type="button" class="ghost" data-action="pull-config">Pull Config</button>');
          actionButtons.push('<button type="button" class="ghost" data-action="push-config">Push Config</button>');
          actionButtons.push('<button type="button" class="alt" data-action="reboot">Reboot</button>');
        }

        row.innerHTML = `
          <td>
            <div class="device-name">${device.display_name || device.serial}</div>
          </td>
          <td>${device.host_port || device.serial}</td>
          <td><span class="badge ${isConnected ? "good square" : "bad"}">${isConnected ? "✓" : device.state}</span></td>
          <td><span class="badge ${isConnected ? "good" : "neutral"}">${isConnected ? "Active" : "Saved"}</span></td>
          <td>${device.pogo_version || "-"}</td>
          <td>${device.memory || "-"}</td>
          <td><div class="action-row">${actionButtons.join("") || '<span class="muted">No actions</span>'}</div></td>
        `;

        row.onclick = () => {
          state.selectedSerial = device.serial;
          $("selectedText").textContent = device.serial;
          setStatus("Selected " + device.serial, "good");
          renderDevices();
        };

        row.querySelectorAll("[data-action]").forEach((button) => {
          button.onclick = async (event) => {
            event.stopPropagation();
            const action = button.dataset.action;
            if (action === "connect") {
              await connectSavedDevice(device.serial);
              return;
            }
            if (action === "update-pogo") {
              await openVersionPicker(device.serial);
              return;
            }
            if (action === "update-cosmog") {
              await deviceAction("Updating Cosmog...", "/api/update_cosmog_zip", {
                serial: device.serial,
                remote_dir: currentRemoteDir(),
              });
              return;
            }
            if (action === "start-cosmog") {
              await deviceAction("Starting Cosmog...", "/api/start_cosmog", {
                serial: device.serial,
                remote_dir: currentRemoteDir(),
              });
              return;
            }
            if (action === "stop-cosmog") {
              await deviceAction("Stopping Cosmog...", "/api/stop_cosmog", {
                serial: device.serial,
                remote_dir: currentRemoteDir(),
              });
              return;
            }
            if (action === "cosmog-log") {
              await deviceAction("Loading Cosmog log...", "/api/cosmog_log", {
                serial: device.serial,
              });
              return;
            }
            if (action === "restart") {
              await deviceAction("Restarting Cosmog...", "/api/restart_cosmog", {
                serial: device.serial,
                remote_dir: currentRemoteDir(),
              });
              return;
            }
            if (action === "pull-config") {
              await pullConfig(device.serial);
              return;
            }
            if (action === "push-config") {
              await openPushConfig(device.serial);
              return;
            }
            if (action === "reboot") {
              await deviceAction("Rebooting device...", "/api/reboot_device", {
                serial: device.serial,
              });
            }
          };
        });

        tableBody.appendChild(row);
      }

      const connected = state.devices.filter((d) => d.state === "device").length;
      $("deviceCount").textContent = String(state.devices.length);
      $("selectedText").textContent = state.selectedSerial || "none";
      $("overviewState").textContent = connected ? "Connected" : "Offline";
      $("overviewState").className = connected ? "chip" : "chip offline";
      $("overviewUpdated").textContent = "Last updated just now";
    }

    async function refreshStatus() {
      const data = await api("/api/status");
      state.devices = data.devices || [];
      if (state.selectedSerial && !state.devices.some((d) => d.serial === state.selectedSerial)) {
        state.selectedSerial = "";
      }
      if (!state.selectedSerial && state.devices.length === 1) {
        state.selectedSerial = state.devices[0].serial;
      }
      $("adbVersion").textContent = data.adb_version || "ready";
      renderDevices();
    }

    async function loadVersions() {
      const data = await api("/api/versions");
      state.versions = (data.versions || []).filter((item) => item.arch === "arm64-v8a");
    }

    async function withAction(buttonId, message, fn) {
      const button = $(buttonId);
      button.disabled = true;
      setStatus(message);
      try {
        const data = await fn();
        setStatus(data.message || "Done", "good");
        appendLog(data.output);
        return data;
      } catch (err) {
        setStatus(err.message, "bad");
        appendLog(err.stack || err.message);
        throw err;
      } finally {
        button.disabled = false;
      }
    }

    async function deviceAction(message, path, body) {
      setStatus(message);
      try {
        const data = await api(path, "POST", body);
        setStatus(data.message || "Done", "good");
        appendLog(data.output);
        await refreshStatus();
        return data;
      } catch (err) {
        setStatus(err.message, "bad");
        appendLog(err.stack || err.message);
        throw err;
      }
    }

    async function connectSavedDevice(serial) {
      return withAction("refreshBtn", "Connecting saved device...", async () => {
        const data = await api("/api/connect_saved", "POST", { serial });
        await refreshStatus();
        return data;
      });
    }

    async function connectFromFields() {
      const host = $("host").value.trim();
      const port = $("port").value.trim() || "5555";
      return withAction("connectBtn", "Connecting device...", async () => {
        const data = await api("/api/connect", "POST", { host, port });
        await refreshStatus();
        return data;
      });
    }

    async function pullConfig(serial) {
      setStatus("Pulling config...");
      try {
        const data = await api("/api/pull_config", "POST", {
          serial,
          remote_dir: currentRemoteDir(),
        });
        setStatus(data.message || "Config pulled", "good");
        appendLog("--- config.toml from " + serial + " ---\\n" + (data.config || "") + "\\n" + (data.output || ""));
        state.pendingPushConfigSerial = serial;
        $("pushConfigText").value = data.config || "";
        $("pushConfigModal").classList.add("open");
        await refreshStatus();
      } catch (err) {
        setStatus(err.message, "bad");
        appendLog(err.stack || err.message);
      }
    }

    function closePushConfig() {
      $("pushConfigModal").classList.remove("open");
      state.pendingPushConfigSerial = "";
      $("pushConfigText").value = "";
    }

    async function openPushConfig(serial) {
      state.pendingPushConfigSerial = serial;
      $("pushConfigText").value = "";
      $("pushConfigModal").classList.add("open");
    }

    function closeVersionPicker() {
      $("versionModal").classList.remove("open");
      state.pendingPogoSerial = "";
    }

    async function openVersionPicker(serial) {
      if (!state.versions.length) {
        await loadVersions();
      }
      const select = $("versionSelect");
      select.innerHTML = "";
      for (const item of state.versions) {
        const option = document.createElement("option");
        option.value = item.version;
        option.textContent = item.version;
        select.appendChild(option);
      }
      if (!state.versions.length) {
        throw new Error("No mirror versions found");
      }
      state.pendingPogoSerial = serial;
      $("versionModal").classList.add("open");
    }

    async function boot() {
      const defaults = await api("/api/defaults");
      state.defaults = defaults;
      $("remoteDir").value = defaults.remote_dir || "/data/adb/cosmog2";
      await refreshStatus();
      appendLog("Panel ready.");
    }

    $("refreshBtn").onclick = () => withAction("refreshBtn", "Refreshing ADB state...", async () => {
      await refreshStatus();
      return { message: "ADB device list refreshed" };
    });

    $("connectBtn").onclick = () => connectFromFields();
    $("versionCancelBtn").onclick = () => closeVersionPicker();
    $("versionConfirmBtn").onclick = async () => {
      const serial = state.pendingPogoSerial;
      const version = $("versionSelect").value;
      closeVersionPicker();
      await deviceAction("Updating PoGo...", "/api/update_pogo_version", {
        serial,
        version,
        arch: "arm64-v8a",
        remote_dir: currentRemoteDir(),
      });
    };
    $("versionModal").onclick = (event) => {
      if (event.target === $("versionModal")) {
        closeVersionPicker();
      }
    };
    $("pushConfigCancelBtn").onclick = () => closePushConfig();
    $("pushConfigConfirmBtn").onclick = async () => {
      const serial = state.pendingPushConfigSerial;
      const configText = $("pushConfigText").value;
      if (!configText.trim()) {
        setStatus("Config content is empty", "bad");
        return;
      }
      closePushConfig();
      const pushResult = await deviceAction("Pushing config...", "/api/push_config", {
        serial,
        config: configText,
        remote_dir: currentRemoteDir(),
      });
      appendLog("Pushed to: " + (pushResult.config_path || "unknown"));
      await deviceAction("Restarting Cosmog to apply config...", "/api/restart_cosmog", {
        serial,
        remote_dir: currentRemoteDir(),
      });
    };
    $("pushConfigModal").onclick = (event) => {
      if (event.target === $("pushConfigModal")) {
        closePushConfig();
      }
    };

    boot().catch((err) => {
      setStatus(err.message, "bad");
      appendLog(err.stack || err.message);
    });
  </script>
</body>
</html>
"""


class ADBConnectionPool:
    def __init__(self) -> None:
        self.connected_devices: set[str] = set()
        self.last_command_time: dict[str, float] = {}

    def note_success(self, serial: str) -> None:
        self.connected_devices.add(serial)
        self.last_command_time[serial] = time.time()

    def note_disconnect(self, serial: str) -> None:
        self.connected_devices.discard(serial)
        self.last_command_time.pop(serial, None)

    def recently_seen(self, serial: str, threshold: int = 30) -> bool:
        return (time.time() - self.last_command_time.get(serial, 0)) < threshold


class DevicePanel:
    MIRROR_URL = "https://mirror.unownhash.com"
    MIRROR_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/135.0 Safari/537.36"
        )
    }

    def __init__(self, base_apk: str, split_apk: str, plugin_so: str, workspace_dir: str, remote_dir: str):
        self.remote_dir = remote_dir
        self.adb_pool = ADBConnectionPool()
        self.workspace_dir = pathlib.Path(workspace_dir)
        self.config_dir = self.workspace_dir / "device_configs"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.download_dir = self.workspace_dir / "downloads"
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.known_devices_path = self.workspace_dir / "known_devices.json"
        self.apk_dir = self.workspace_dir / "apks"
        self.apk_dir.mkdir(parents=True, exist_ok=True)
        self.plugin_dir = self.workspace_dir / "lib"
        self.plugin_dir.mkdir(parents=True, exist_ok=True)
        self.cosmog_updates_dir = self.workspace_dir / "cosmog_updates"
        self.cosmog_updates_dir.mkdir(parents=True, exist_ok=True)
        self.base_apk_dir = self.workspace_dir / "base_apks"
        self.base_apk_dir.mkdir(parents=True, exist_ok=True)
        self.split_apk_dir = self.workspace_dir / "split_apks"
        self.split_apk_dir.mkdir(parents=True, exist_ok=True)
        self.plugin_store_dir = self.workspace_dir / "plugin_libs"
        self.plugin_store_dir.mkdir(parents=True, exist_ok=True)
        self.cosmog_zip_dir = self.workspace_dir / "cosmog_zips"
        self.cosmog_zip_dir.mkdir(parents=True, exist_ok=True)
        self.device_info_cache: dict[str, tuple[float, dict[str, str]]] = {}
        self.base_apk = self.resolve_default_asset(
            explicit_path=base_apk,
            preferred_dir=self.base_apk_dir,
            label="Base APK",
            pattern="*.apk",
        )
        self.split_apk = self.resolve_default_asset(
            explicit_path=split_apk,
            preferred_dir=self.split_apk_dir,
            label="Split APK",
            pattern="*.apk",
        )
        self.plugin_so = self.resolve_default_asset(
            explicit_path=plugin_so,
            preferred_dir=self.plugin_store_dir,
            label="Plugin library",
            pattern="*.so",
        )

    def run(self, args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
        logging.debug("Running command: %s", " ".join(args))
        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=check,
        )

    def run_adb(self, serial: str | None, adb_args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
        args = ["adb"]
        if serial:
            args.extend(["-s", serial])
        args.extend(adb_args)
        result = self.run(args, check=check)
        if serial and result.returncode == 0:
            self.adb_pool.note_success(serial)
        return result

    def run_root_shell(self, serial: str, command: str, *, check: bool = True) -> subprocess.CompletedProcess[str]:
        return self.run_adb(serial, ["shell", f"su -c {shlex.quote(command)}"], check=check)

    def adb_version(self) -> str:
        result = self.run(["adb", "version"])
        return result.stdout.splitlines()[0].replace("Android Debug Bridge version ", "")

    def ensure_connected(self, serial: str) -> bool:
        serial = serial.strip()
        if self.adb_pool.recently_seen(serial):
            return True

        devices = self.run(["adb", "devices"], check=False)
        if f"{serial}\tdevice" in devices.stdout:
            self.adb_pool.note_success(serial)
            return True

        if ":" in serial:
            connect = self.run(["adb", "connect", serial], check=False)
            verify = self.run(["adb", "devices"], check=False)
            if connect.returncode == 0 and f"{serial}\tdevice" in verify.stdout:
                self.adb_pool.note_success(serial)
                return True

        self.adb_pool.note_disconnect(serial)
        return False

    def fetch_json(self, url: str) -> list[dict]:
        request = Request(url, headers=self.MIRROR_HEADERS)
        with urlopen(request) as response:
            return json.load(response)

    def parse_version_key(self, version: str) -> tuple[int, ...]:
        return tuple(int(part) for part in version.replace(".apkm", "").split("."))

    def resolve_default_asset(
        self,
        *,
        explicit_path: str | None,
        preferred_dir: pathlib.Path,
        label: str,
        pattern: str,
    ) -> str:
        if explicit_path and explicit_path.strip():
            candidate = pathlib.Path(explicit_path).expanduser()
            if candidate.is_file():
                return str(candidate)
        matches = sorted(
            (path for path in preferred_dir.glob(pattern) if path.is_file()),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        return str(matches[0]) if matches else ""

    def setup_paths(self) -> dict[str, str]:
        return {
            "base_apk_dir": str(self.base_apk_dir),
            "split_apk_dir": str(self.split_apk_dir),
            "plugin_dir": str(self.plugin_store_dir),
            "cosmog_zip_dir": str(self.cosmog_zip_dir),
        }

    def default_cosmog_zip(self) -> str:
        return self.resolve_default_asset(
            explicit_path="",
            preferred_dir=self.cosmog_zip_dir,
            label="Cosmog ZIP",
            pattern="*.zip",
        )

    def load_known_devices(self) -> dict[str, dict[str, str]]:
        if not self.known_devices_path.exists():
            return {}
        try:
            with open(self.known_devices_path, "r", encoding="utf-8") as handle:
                raw = json.load(handle)
        except (json.JSONDecodeError, OSError):
            logging.warning("Failed to load known devices from %s", self.known_devices_path)
            return {}

        known: dict[str, dict[str, str]] = {}
        if not isinstance(raw, list):
            return known

        for item in raw:
            if not isinstance(item, dict):
                continue
            serial = str(item.get("serial", "")).strip()
            host = str(item.get("host", "")).strip()
            port = str(item.get("port", "")).strip()
            if not serial or not host or not port:
                continue
            known[serial] = {
                "serial": serial,
                "host": host,
                "port": port,
            }
        return known

    def save_known_devices(self, known: dict[str, dict[str, str]]) -> None:
        payload = sorted(known.values(), key=lambda item: item["serial"])
        with open(self.known_devices_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)

    def remember_network_device(self, host: str, port: str) -> str:
        host = host.strip()
        port = str(port).strip() or "5555"
        serial = f"{host}:{port}"
        known = self.load_known_devices()
        known[serial] = {
            "serial": serial,
            "host": host,
            "port": port,
        }
        self.save_known_devices(known)
        return serial

    def list_mirror_versions(self) -> list[dict[str, str]]:
        versions = self.fetch_json(f"{self.MIRROR_URL}/index.json")
        normalized = []
        for item in versions:
            version = item["version"].replace(".apkm", "")
            normalized.append(
                {
                    "version": version,
                    "arch": item["arch"],
                    "filename": item["filename"],
                }
            )
        normalized.sort(key=lambda item: (item["arch"], self.parse_version_key(item["version"])), reverse=True)
        return normalized

    def find_version(self, version: str, arch: str) -> dict[str, str]:
        for item in self.list_mirror_versions():
            if item["version"] == version and item["arch"] == arch:
                return item
        raise ValueError(f"Version {version} for {arch} was not found on the mirror")

    def find_split_name(self, members: list[str], arch: str) -> str:
        exact = f"split_config.{arch.replace('-', '_')}.apk"
        for name in members:
            if os.path.basename(name) == exact:
                return name
        for name in members:
            base = os.path.basename(name)
            if base.startswith("split_config.") and base.endswith(".apk"):
                return name
        raise FileNotFoundError("split_config APK not found in archive")

    def plugin_output_path(self, arch: str, version: str) -> pathlib.Path:
        plugin_path = self.plugin_dir / "libNianticLabsPlugin.so"
        return plugin_path

    def apk_output_paths(self, arch: str, version: str, split_name: str) -> tuple[pathlib.Path, pathlib.Path]:
        base_path = self.base_apk_dir / "base.apk"
        split_path = self.split_apk_dir / os.path.basename(split_name)
        return base_path, split_path

    def download_version(self, version: str, arch: str) -> dict[str, object]:
        if not version:
            raise ValueError("Version is required")

        item = self.find_version(version, arch)
        version_dir = self.download_dir / f"{arch}_{version}"
        version_dir.mkdir(parents=True, exist_ok=True)

        archive_path = version_dir / item["filename"]
        download_url = f"{self.MIRROR_URL}/apks/{item['filename']}"
        request = Request(download_url, headers=self.MIRROR_HEADERS)
        with urlopen(request) as response, open(archive_path, "wb") as out:
            out.write(response.read())

        with zipfile.ZipFile(archive_path) as outer_zip:
            members = outer_zip.namelist()
            base_name = "base.apk"
            split_name = self.find_split_name(members, arch)
            extracted_base, extracted_split = self.apk_output_paths(arch, version, split_name)
            with outer_zip.open(base_name) as src, open(extracted_base, "wb") as dst:
                dst.write(src.read())
            with outer_zip.open(split_name) as src, open(extracted_split, "wb") as dst:
                dst.write(src.read())

        self.base_apk = str(extracted_base)
        self.split_apk = str(extracted_split)

        return {
            "message": f"Downloaded and extracted {version} for {arch}",
            "output": f"Archive: {archive_path}\nBase APK: {extracted_base}\nSplit APK: {extracted_split}",
            "paths": {
                "base_apk": str(extracted_base),
                "split_apk": str(extracted_split),
            },
        }

    def list_devices(self) -> list[dict[str, str]]:
        result = self.run(["adb", "devices", "-l"], check=False)
        devices: list[dict[str, str]] = []
        known_network = self.load_known_devices()
        seen_serials: set[str] = set()
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line or line.startswith("List of devices attached"):
                continue
            parts = line.split()
            serial = parts[0]
            seen_serials.add(serial)
            state = parts[1] if len(parts) > 1 else "unknown"
            details = " ".join(parts[2:]) if len(parts) > 2 else ""
            if state == "device":
                self.adb_pool.note_success(serial)
            else:
                self.adb_pool.note_disconnect(serial)
            metadata = self.device_metadata(serial, state, details)
            devices.append(
                {
                    "serial": serial,
                    "display_name": metadata["name"],
                    "state": state,
                    "details": details,
                    "host_port": serial,
                    "connection_type": "network" if ":" in serial else "usb",
                    "pogo_version": metadata["pogo_version"],
                    "memory": metadata["memory"],
                }
            )
        for serial, saved in known_network.items():
            if serial in seen_serials:
                continue
            devices.append(
                {
                    "serial": serial,
                    "display_name": saved["host"],
                    "state": "saved",
                    "details": f"Saved target on port {saved['port']}. Click Connect to reconnect.",
                    "host_port": serial,
                    "connection_type": "network",
                    "pogo_version": "-",
                    "memory": "-",
                }
            )
        devices.sort(key=lambda item: (item["state"] != "device", item["connection_type"] != "network", item["serial"]))
        return devices

    def device_metadata(self, serial: str, state: str, details: str) -> dict[str, str]:
        fallback_name = self.parse_device_name(serial, details)
        empty = {
            "name": fallback_name,
            "pogo_version": "-",
            "memory": "-",
        }
        if state != "device":
            return empty

        cached = self.device_info_cache.get(serial)
        if cached and (time.time() - cached[0]) < 20:
            return cached[1]

        metadata = dict(empty)

        try:
            package_info = self.run_adb(serial, ["shell", "dumpsys", "package", "com.nianticlabs.pokemongo"], check=False)
            for line in package_info.stdout.splitlines():
                line = line.strip()
                if line.startswith("versionName="):
                    metadata["pogo_version"] = line.split("=", 1)[1].strip() or "-"
                    break
        except Exception:
            pass

        try:
            meminfo = self.run_adb(serial, ["shell", "cat", "/proc/meminfo"], check=False)
            for line in meminfo.stdout.splitlines():
                if line.startswith("MemTotal:"):
                    parts = line.split()
                    if len(parts) >= 2 and parts[1].isdigit():
                        mem_kb = int(parts[1])
                        metadata["memory"] = f"{mem_kb / 1024 / 1024:.2f} GB"
                    break
        except Exception:
            pass

        self.device_info_cache[serial] = (time.time(), metadata)
        return metadata

    def parse_device_name(self, serial: str, details: str) -> str:
        for token in details.split():
            if token.startswith("model:"):
                return token.split(":", 1)[1].replace("_", " ")
        return serial.split(":")[0]

    def connect(self, host: str, port: str) -> dict[str, str]:
        if not host:
            raise ValueError("Host is required")
        target = self.remember_network_device(host, port)
        result = self.run(["adb", "connect", target], check=False)
        if result.returncode == 0:
            self.adb_pool.note_success(target)
        return {
            "message": f"Connect requested for {target}",
            "output": (result.stdout + result.stderr).strip(),
        }

    def connect_saved(self, serial: str) -> dict[str, str]:
        serial = serial.strip()
        if not serial:
            raise ValueError("Saved device serial is required")
        known = self.load_known_devices()
        device = known.get(serial)
        if not device:
            raise FileNotFoundError(f"Saved device not found: {serial}")
        return self.connect(device["host"], device["port"])

    def ensure_file(self, path: str, label: str) -> str:
        if not path:
            raise ValueError(f"{label} path is required")
        if not os.path.isfile(path):
            raise FileNotFoundError(f"{label} not found: {path}")
        return path

    def resolve_zip_input(self, path: str, label: str) -> pathlib.Path:
        if not path or not path.strip():
            raise ValueError(f"{label} path is required")

        candidate = pathlib.Path(path.strip()).expanduser()
        if candidate.is_file():
            return candidate

        if candidate.is_dir():
            zip_files = sorted(p for p in candidate.iterdir() if p.is_file() and p.suffix.lower() == ".zip")
            if len(zip_files) == 1:
                return zip_files[0]
            if not zip_files:
                raise FileNotFoundError(f"{label} directory contains no .zip files: {candidate}")
            raise ValueError(f"{label} directory contains multiple .zip files; paste the exact ZIP path")

        raise FileNotFoundError(f"{label} not found: {candidate}")

    def normalize_remote_dir(self, remote_dir: str | None) -> str:
        value = (remote_dir or self.remote_dir).strip()
        if not value:
            raise ValueError("Remote directory is required")
        return value.rstrip("/")

    def download_plugin(self, version: str, arch: str) -> dict[str, object]:
        if not version:
            raise ValueError("Version is required")

        item = self.find_version(version, arch)
        version_dir = self.download_dir / f"{arch}_{version}"
        version_dir.mkdir(parents=True, exist_ok=True)
        archive_path = version_dir / item["filename"]
        download_url = f"{self.MIRROR_URL}/apks/{item['filename']}"

        if not archive_path.exists():
            request = Request(download_url, headers=self.MIRROR_HEADERS)
            with urlopen(request) as response, open(archive_path, "wb") as out:
                out.write(response.read())

        plugin_path = self.plugin_store_dir / "libNianticLabsPlugin.so"
        member_name = f"lib/{arch}/libNianticLabsPlugin.so"

        with zipfile.ZipFile(archive_path) as outer_zip:
            if archive_path.suffix == ".apkm":
                split_name = self.find_split_name(outer_zip.namelist(), arch)
                with outer_zip.open(split_name) as split_stream:
                    split_bytes = split_stream.read()
                with zipfile.ZipFile(io.BytesIO(split_bytes)) as split_zip:
                    with split_zip.open(member_name) as src, open(plugin_path, "wb") as dst:
                        dst.write(src.read())
            else:
                with outer_zip.open(member_name) as src, open(plugin_path, "wb") as dst:
                    dst.write(src.read())

        self.plugin_so = self.ensure_file(str(plugin_path), "Plugin library")
        return {
            "message": f"Plugin extracted for {version} ({arch})",
            "output": f"Archive: {archive_path}\nPlugin: {self.plugin_so}",
            "paths": {
                "plugin_so": self.plugin_so,
            },
        }

    def push_tmp(self, serial: str, paths: dict[str, str]) -> dict[str, str]:
        base_apk = self.ensure_file(paths.get("base_apk") or self.resolve_default_asset(explicit_path=self.base_apk, preferred_dir=self.base_apk_dir, label="Base APK", pattern="*.apk"), "Base APK")
        split_apk = self.ensure_file(paths.get("split_apk") or self.resolve_default_asset(explicit_path=self.split_apk, preferred_dir=self.split_apk_dir, label="Split APK", pattern="*.apk"), "Split APK")
        plugin_so = self.ensure_file(paths.get("plugin_so") or self.resolve_default_asset(explicit_path=self.plugin_so, preferred_dir=self.plugin_store_dir, label="Plugin library", pattern="*.so"), "Plugin library")
        self.base_apk = base_apk
        self.split_apk = split_apk
        self.plugin_so = plugin_so

        base_tmp = f"/data/local/tmp/{os.path.basename(base_apk)}"
        split_tmp = f"/data/local/tmp/{os.path.basename(split_apk)}"
        plugin_tmp = f"/data/local/tmp/{os.path.basename(plugin_so)}"

        outputs = []
        cleanup = self.run_adb(serial, ["shell", "rm", "-f", base_tmp, split_tmp, plugin_tmp], check=False)
        cleanup_text = (cleanup.stdout + cleanup.stderr).strip()
        if cleanup_text:
            outputs.append(cleanup_text)
        outputs.append(self.run_adb(serial, ["push", base_apk, base_tmp]).stdout.strip())
        outputs.append(self.run_adb(serial, ["push", split_apk, split_tmp]).stdout.strip())
        outputs.append(self.run_adb(serial, ["push", plugin_so, plugin_tmp]).stdout.strip())
        return {
            "message": f"Payload files pushed to /data/local/tmp on {serial}",
            "output": "\n".join(filter(None, outputs)),
            "tmp_paths": {
                "base_apk": base_tmp,
                "split_apk": split_tmp,
                "plugin_so": plugin_tmp,
            },
        }

    def deploy_payload(self, serial: str, paths: dict[str, str], remote_dir: str | None = None) -> dict[str, str]:
        staged = self.push_tmp(serial, paths)
        installed = self.install_payload(serial, staged["tmp_paths"], remote_dir)
        return {
            "message": installed["message"],
            "output": "\n\n".join(part for part in [staged.get("output", ""), installed.get("output", "")] if part),
        }

    def update_pogo_version(self, serial: str, version: str, arch: str = "arm64-v8a", remote_dir: str | None = None) -> dict[str, str]:
        downloaded = self.download_version(version, arch)
        plugin = self.download_plugin(version, arch)
        stopped = self.stop_cosmog(serial, remote_dir)
        time.sleep(1)
        deployed = self.deploy_payload(serial, {}, remote_dir)
        started = self.start_cosmog(serial, remote_dir)
        return {
            "message": f"PoGo {version} updated on {serial}",
            "output": "\n\n".join(
                part for part in [
                    downloaded.get("output", ""),
                    plugin.get("output", ""),
                    stopped.get("output", ""),
                    deployed.get("output", ""),
                    started.get("output", ""),
                ] if part
            ),
        }

    def install_payload(self, serial: str, tmp_paths: dict[str, str], remote_dir: str | None = None) -> dict[str, str]:
        remote_dir = self.normalize_remote_dir(remote_dir)
        base_tmp = tmp_paths["base_apk"]
        split_tmp = tmp_paths["split_apk"]
        plugin_tmp = tmp_paths["plugin_so"]
        plugin_name = os.path.basename(plugin_tmp)
        commands = [
            f"mkdir -p {remote_dir}/files {remote_dir}/lib",
            f"rm -f {remote_dir}/files/*.apk",
            f"rm -f {remote_dir}/lib/{plugin_name}",
            f"mv {base_tmp} {remote_dir}/files/",
            f"mv {split_tmp} {remote_dir}/files/",
            f"chmod 644 {remote_dir}/files/*.apk",
            f"chown system:system {remote_dir}/files/*.apk",
            f"mv {plugin_tmp} {remote_dir}/lib/",
            f"chmod 755 {remote_dir}/lib/{plugin_name}",
            f"chown system:system {remote_dir}/lib/{plugin_name}",
            f"ls -la {remote_dir}/lib/{plugin_name}",
        ]
        outputs = []
        for cmd in commands:
            result = self.run_root_shell(serial, cmd)
            chunk = (result.stdout + result.stderr).strip()
            if chunk:
                outputs.append(f"$ {cmd}\n{chunk}")
            else:
                outputs.append(f"$ {cmd}\nOK")
        return {
            "message": f"Payload installed into {remote_dir} on {serial}",
            "output": "\n\n".join(outputs),
        }

    def extract_cosmog_zip(self, zip_path: str) -> tuple[pathlib.Path, list[pathlib.Path], pathlib.Path, pathlib.Path | None]:
        archive_path = self.resolve_zip_input(zip_path, "Cosmog ZIP")
        extract_dir = self.cosmog_updates_dir / archive_path.stem

        if extract_dir.exists():
            for path in sorted(extract_dir.rglob("*"), reverse=True):
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    path.rmdir()
        extract_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(archive_path) as zf:
            members = zf.namelist()

            launcher_members = [
                name for name in members
                if not name.endswith("/") and os.path.basename(name).startswith("com.nianticlabs.")
            ]
            if not launcher_members:
                raise FileNotFoundError("No com.nianticlabs.* executable found in Cosmog ZIP")

            launcher_member = launcher_members[0]
            launcher_path = extract_dir / os.path.basename(launcher_member)
            with zf.open(launcher_member) as src, open(launcher_path, "wb") as dst:
                dst.write(src.read())

            lib_members = [
                name for name in members
                if name.startswith("lib/") and not name.endswith("/")
            ]
            if not lib_members:
                raise FileNotFoundError("No files found under lib/ in Cosmog ZIP")

            lib_dir = extract_dir / "lib"
            lib_dir.mkdir(parents=True, exist_ok=True)
            libs: list[pathlib.Path] = []
            for member in lib_members:
                dest = lib_dir / os.path.basename(member)
                with zf.open(member) as src, open(dest, "wb") as dst:
                    dst.write(src.read())
                libs.append(dest)

            config_members = [
                name for name in members
                if not name.endswith("/") and name.rstrip("/").count("/") == 0
                and os.path.basename(name) in ("config.toml", "config.toml.example")
            ]
            config_path: pathlib.Path | None = None
            if config_members:
                config_path = extract_dir / "config.toml"
                with zf.open(config_members[0]) as src, open(config_path, "wb") as dst:
                    dst.write(src.read())

        return launcher_path, libs, config_path, extract_dir

    def update_cosmog_zip(self, serial: str, zip_path: str, remote_dir: str | None = None) -> dict[str, str]:
        remote_dir = self.normalize_remote_dir(remote_dir)
        launcher_path, libs, config_path, extract_dir = self.extract_cosmog_zip(zip_path or self.default_cosmog_zip())
        remote_launcher_name = "com.nianticlabs.pokemongo"

        outputs = []
        prep = self.run_root_shell(serial, f"mkdir -p {remote_dir}/lib")
        prep_text = (prep.stdout + prep.stderr).strip()
        if prep_text:
            outputs.append(prep_text)

        tmp_launcher = f"/data/local/tmp/{launcher_path.name}"
        push_exec = self.run_adb(serial, ["push", str(launcher_path), tmp_launcher])
        outputs.append((push_exec.stdout + push_exec.stderr).strip())

        for lib_path in libs:
            tmp_lib = f"/data/local/tmp/{lib_path.name}"
            result = self.run_adb(serial, ["push", str(lib_path), tmp_lib])
            outputs.append((result.stdout + result.stderr).strip())

        tmp_config: str | None = None
        if config_path is not None:
            tmp_config = f"/data/local/tmp/config.toml"
            result = self.run_adb(serial, ["push", str(config_path), tmp_config])
            outputs.append((result.stdout + result.stderr).strip())

        commands = [
            f"rm -f {remote_dir}/{remote_launcher_name}",
            f"mv {tmp_launcher} {remote_dir}/{remote_launcher_name}",
            f"chmod 755 {remote_dir}/{remote_launcher_name}",
            f"chown system:system {remote_dir}/{remote_launcher_name}",
        ]
        for lib_path in libs:
            commands.append(f"mv /data/local/tmp/{lib_path.name} {remote_dir}/lib/{lib_path.name}")
            commands.append(f"chmod 755 {remote_dir}/lib/{lib_path.name}")
            commands.append(f"chown system:system {remote_dir}/lib/{lib_path.name}")

        if tmp_config is not None:
            commands.append(f"rm -f {remote_dir}/config.toml")
            commands.append(f"mv {tmp_config} {remote_dir}/config.toml")
            commands.append(f"chmod 644 {remote_dir}/config.toml")
            commands.append(f"chown system:system {remote_dir}/config.toml")

        for cmd in commands:
            result = self.run_root_shell(serial, cmd)
            chunk = (result.stdout + result.stderr).strip()
            outputs.append(f"$ {cmd}\n{chunk or 'OK'}")

        return {
            "message": f"Cosmog updated from ZIP into {remote_dir} on {serial}",
            "output": "\n\n".join(
                [
                    f"Extracted to: {extract_dir}",
                    f"Launcher: {launcher_path}",
                    f"Installed launcher name: {remote_launcher_name}",
                    "Libraries: " + ", ".join(str(path) for path in libs),
                    f"Config: {'installed' if config_path else 'not in ZIP'}",
                ]
                + [part for part in outputs if part]
            ),
        }

    def start_cosmog(self, serial: str, remote_dir: str | None = None) -> dict[str, str]:
        remote_dir = self.normalize_remote_dir(remote_dir)
        cmd = (
            f"cd {remote_dir} && "
            "setsid sh -c './com.nianticlabs.pokemongo >/data/local/tmp/cosmog.out 2>&1' >/dev/null 2>&1 < /dev/null & "
            "echo started"
        )
        adb_args = ["adb", "-s", serial, "shell", f"su -c {shlex.quote(cmd)}"]
        logging.debug("Starting cosmog asynchronously: %s", " ".join(adb_args))
        subprocess.Popen(
            adb_args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
        return {
            "message": f"Start command sent in {remote_dir} on {serial}",
            "output": "Cosmog start launched in background",
        }

    def stop_cosmog(self, serial: str, remote_dir: str | None = None) -> dict[str, str]:
        remote_dir = self.normalize_remote_dir(remote_dir)
        cmd = (
            "pkill -f '/com.nianticlabs.pokemongo' "
            "|| pkill -f 'com.nianticlabs.pokemongo' "
            "|| true; echo stopped"
        )
        result = self.run_root_shell(serial, cmd, check=False)
        output = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
        return {
            "message": f"Stop command sent in {remote_dir} on {serial}",
            "output": output or "Cosmog stop command executed",
        }

    def restart_cosmog(self, serial: str, remote_dir: str | None = None) -> dict[str, str]:
        stopped = self.stop_cosmog(serial, remote_dir)
        time.sleep(1)
        started = self.start_cosmog(serial, remote_dir)
        return {
            "message": f"Cosmog restarted on {serial}",
            "output": "\n\n".join(part for part in [stopped.get("output", ""), started.get("output", "")] if part),
        }

    def reboot_device(self, serial: str) -> dict[str, str]:
        result = self.run_adb(serial, ["reboot"], check=False)
        self.adb_pool.note_disconnect(serial)
        self.device_info_cache.pop(serial, None)
        output = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
        return {
            "message": f"Reboot requested for {serial}",
            "output": output or "Device reboot command sent",
        }

    def cosmog_log(self, serial: str) -> dict[str, str]:
        result = self.run_adb(
            serial,
            ["shell", "su", "-c", "tail -n 200 /data/local/tmp/cosmog.out"],
            check=False,
        )
        output = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
        return {
            "message": f"Loaded Cosmog log from {serial}",
            "output": output or "No log output found in /data/local/tmp/cosmog.out",
        }

    def config_cache_path(self, serial: str) -> pathlib.Path:
        safe = "".join(ch if ch.isalnum() or ch in "-._" else "_" for ch in serial)
        return self.config_dir / f"{safe}.config.toml"

    def pull_config(self, serial: str, remote_dir: str | None = None) -> dict[str, str]:
        remote_dir = self.normalize_remote_dir(remote_dir)
        cache_path = self.config_cache_path(serial)
        remote_tmp = f"/data/local/tmp/{cache_path.name}"

        steps = []
        # Delete old cached config on host before pulling fresh
        if cache_path.exists():
            cache_path.unlink()
            steps.append("deleted old cached config on host")
        # Delete old temp file on device before copying fresh
        self.run_root_shell(serial, f"rm -f {remote_tmp}", check=False)
        result = self.run_root_shell(serial, f"cp {remote_dir}/config.toml {remote_tmp} && chmod 644 {remote_tmp}")
        steps.append((result.stdout + result.stderr).strip() or "copied to tmp on device")
        result = self.run_adb(serial, ["pull", remote_tmp, str(cache_path)])
        steps.append((result.stdout + result.stderr).strip())
        try:
            cleanup = self.run_adb(serial, ["shell", "rm", "-f", remote_tmp], check=False)
            cleanup_text = (cleanup.stdout + cleanup.stderr).strip()
            if cleanup_text:
                steps.append(cleanup_text)
        except Exception:
            pass

        config_text = cache_path.read_text(encoding="utf-8")
        return {
            "message": f"Config pulled from {serial}",
            "output": "\n".join(filter(None, steps)),
            "config": config_text,
        }

    def push_config(self, serial: str, config_text: str, remote_dir: str | None = None) -> dict[str, str]:
        if not config_text.strip():
            raise ValueError("Config content is empty")
        remote_dir = self.normalize_remote_dir(remote_dir)

        cache_path = self.config_cache_path(serial)
        # Delete old cached config on host before writing fresh
        if cache_path.exists():
            cache_path.unlink()
        cache_path.write_text(config_text, encoding="utf-8")
        remote_tmp = f"/data/local/tmp/{cache_path.name}"

        steps = []
        # Delete old config on device first, then push new
        self.run_root_shell(serial, f"rm -f {remote_dir}/config.toml {remote_tmp}", check=False)
        result = self.run_adb(serial, ["push", str(cache_path), remote_tmp])
        steps.append((result.stdout + result.stderr).strip())

        commands = [
            f"mv {remote_tmp} {remote_dir}/config.toml",
            f"chmod 644 {remote_dir}/config.toml",
            f"chown system:system {remote_dir}/config.toml",
        ]
        for cmd in commands:
            result = self.run_root_shell(serial, cmd)
            chunk = (result.stdout + result.stderr).strip()
            steps.append(f"$ {cmd}\n{chunk or 'OK'}")

        config_path = f"{remote_dir}/config.toml"
        return {
            "message": f"Config pushed to {serial} at {config_path}",
            "output": "\n\n".join(filter(None, steps)),
            "config_path": config_path,
        }


class Handler(BaseHTTPRequestHandler):
    panel: DevicePanel | None = None

    def log_message(self, fmt: str, *args) -> None:
        logging.info("%s - %s", self.address_string(), fmt % args)

    def send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            logging.info("Client disconnected before JSON response could be sent")

    def send_html(self, content: str) -> None:
        body = content.encode("utf-8")
        try:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            logging.info("Client disconnected before HTML response could be sent")

    def parse_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def ok(self, **kwargs) -> None:
        self.send_json(HTTPStatus.OK, {"ok": True, **kwargs})

    def fail(self, status: int, error: str) -> None:
        self.send_json(status, {"ok": False, "error": error})

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_html(HTML_PAGE)
            return

        if parsed.path == "/api/defaults":
            assert self.panel is not None
            self.ok(
                paths={
                    "base_apk": self.panel.base_apk,
                    "split_apk": self.panel.split_apk,
                    "plugin_so": self.panel.plugin_so,
                },
                setup_paths=self.panel.setup_paths(),
                cosmog_zip=self.panel.default_cosmog_zip(),
                remote_dir=self.panel.remote_dir,
                arch="arm64-v8a",
            )
            return

        if parsed.path == "/api/status":
            assert self.panel is not None
            try:
                self.ok(
                    adb_version=self.panel.adb_version(),
                    devices=self.panel.list_devices(),
                )
            except Exception as exc:
                self.fail(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return

        if parsed.path == "/api/versions":
            assert self.panel is not None
            try:
                self.ok(versions=self.panel.list_mirror_versions())
            except Exception as exc:
                self.fail(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return

        self.fail(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        assert self.panel is not None

        try:
            data = self.parse_json_body()

            if parsed.path == "/api/connect":
                result = self.panel.connect(data.get("host", "").strip(), str(data.get("port", "")).strip() or "5555")
                self.ok(**result)
                return

            if parsed.path == "/api/connect_saved":
                result = self.panel.connect_saved(data.get("serial", ""))
                self.ok(**result)
                return

            if parsed.path == "/api/deploy_payload":
                result = self.panel.deploy_payload(data["serial"], data.get("paths", {}), data.get("remote_dir"))
                self.ok(**result)
                return

            if parsed.path == "/api/update_pogo_version":
                result = self.panel.update_pogo_version(
                    data["serial"],
                    data.get("version", ""),
                    data.get("arch", "arm64-v8a"),
                    data.get("remote_dir"),
                )
                self.ok(**result)
                return

            if parsed.path == "/api/pull_config":
                result = self.panel.pull_config(data["serial"], data.get("remote_dir"))
                self.ok(**result)
                return

            if parsed.path == "/api/push_config":
                result = self.panel.push_config(data["serial"], data.get("config", ""), data.get("remote_dir"))
                self.ok(**result)
                return

            if parsed.path == "/api/download_version":
                result = self.panel.download_version(data.get("version", ""), data.get("arch", "arm64-v8a"))
                self.ok(**result)
                return

            if parsed.path == "/api/download_plugin":
                result = self.panel.download_plugin(data.get("version", ""), data.get("arch", "arm64-v8a"))
                self.ok(**result)
                return

            if parsed.path == "/api/update_cosmog_zip":
                result = self.panel.update_cosmog_zip(
                    data["serial"],
                    data.get("zip_path", ""),
                    data.get("remote_dir"),
                )
                self.ok(**result)
                return

            if parsed.path == "/api/start_cosmog":
                result = self.panel.start_cosmog(
                    data["serial"],
                    data.get("remote_dir"),
                )
                self.ok(**result)
                return

            if parsed.path == "/api/restart_cosmog":
                result = self.panel.restart_cosmog(
                    data["serial"],
                    data.get("remote_dir"),
                )
                self.ok(**result)
                return

            if parsed.path == "/api/stop_cosmog":
                result = self.panel.stop_cosmog(
                    data["serial"],
                    data.get("remote_dir"),
                )
                self.ok(**result)
                return

            if parsed.path == "/api/cosmog_log":
                result = self.panel.cosmog_log(
                    data["serial"],
                )
                self.ok(**result)
                return

            if parsed.path == "/api/reboot_device":
                result = self.panel.reboot_device(
                    data["serial"],
                )
                self.ok(**result)
                return

            self.fail(HTTPStatus.NOT_FOUND, "Not found")
        except subprocess.CalledProcessError as exc:
            output = "\n".join(part for part in [exc.stdout, exc.stderr] if part).strip()
            self.fail(HTTPStatus.BAD_REQUEST, output or str(exc))
        except (KeyError, ValueError, FileNotFoundError) as exc:
            self.fail(HTTPStatus.BAD_REQUEST, str(exc))
        except (BrokenPipeError, ConnectionResetError):
            logging.info("Client disconnected before request completed")
        except Exception as exc:
            logging.exception("Request failed")
            self.fail(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local ADB web panel for Cosmog device management")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP bind host")
    parser.add_argument("--port", type=int, default=8080, help="HTTP bind port")
    parser.add_argument("--base-apk", default="", help="Optional base APK file path override")
    parser.add_argument("--split-apk", default="", help="Optional split APK file path override")
    parser.add_argument("--plugin-so", default="", help="Optional plugin library file path override")
    parser.add_argument("--remote-dir", default="/data/adb/cosmog2", help="Remote Cosmog directory on device")
    parser.add_argument("--workspace", default=".", help="Workspace for cached config files")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    panel = DevicePanel(
        base_apk=args.base_apk,
        split_apk=args.split_apk,
        plugin_so=args.plugin_so,
        workspace_dir=args.workspace,
        remote_dir=args.remote_dir,
    )

    Handler.panel = panel
    server = ThreadingHTTPServer((args.host, args.port), Handler)

    logging.info("Device panel listening on http://%s:%d", args.host, args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
