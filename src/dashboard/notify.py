"""决策推送：企业微信 / 飞书机器人 webhook。

webhook 通过环境变量或 dict 传入，避免密钥入库。
"""

import os

import requests


def _wecom_payload(text: str) -> dict:
    # 企业微信机器人支持 markdown；文本过长截断到 4000 字符
    return {"msgtype": "markdown", "markdown": {"content": text[:4000]}}


def _feishu_payload(text: str) -> dict:
    # 飞书机器人支持 post 富文本；这里用 text（简单）
    return {"msg_type": "text", "content": {"text": text[:4000]}}


def send_wecom(text: str, webhook: str | None = None) -> tuple[bool, str]:
    """发送企业微信机器人消息。"""
    webhook = webhook or os.environ.get("WECOM_WEBHOOK_URL", "")
    if not webhook:
        return False, "未配置 WECOM_WEBHOOK_URL"
    try:
        resp = requests.post(webhook, json=_wecom_payload(text), timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("errcode") == 0:
                return True, "ok"
            return False, f"errcode={data.get('errcode')} {data.get('errmsg')}"
        return False, f"HTTP {resp.status_code}"
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def send_feishu(text: str, webhook: str | None = None) -> tuple[bool, str]:
    """发送飞书机器人消息。"""
    webhook = webhook or os.environ.get("FEISHU_WEBHOOK_URL", "")
    if not webhook:
        return False, "未配置 FEISHU_WEBHOOK_URL"
    try:
        resp = requests.post(webhook, json=_feishu_payload(text), timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("StatusCode") == 0 or data.get("code") == 0:
                return True, "ok"
            return False, f"code={data}"[-200:]
        return False, f"HTTP {resp.status_code}"
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def push_all(
    text: str,
    wecom_webhook: str | None = None,
    feishu_webhook: str | None = None,
) -> dict[str, tuple[bool, str]]:
    """发送到所有已配置的渠道，返回各渠道结果。"""
    results = {}
    if wecom_webhook or os.environ.get("WECOM_WEBHOOK_URL"):
        results["wecom"] = send_wecom(text, wecom_webhook)
    if feishu_webhook or os.environ.get("FEISHU_WEBHOOK_URL"):
        results["feishu"] = send_feishu(text, feishu_webhook)
    return results