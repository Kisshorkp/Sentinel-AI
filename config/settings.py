"""Application settings loaded from environment variables."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class DataSource(str, Enum):
    SAMPLE = "sample"
    CSV = "csv"


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_title: str = Field(default="Sentinel AI", alias="APP_TITLE")
    app_currency: str = Field(default="USD", alias="APP_CURRENCY")
    warning_threshold_pct: float = Field(default=80.0, alias="WARNING_THRESHOLD_PCT")
    critical_threshold_pct: float = Field(default=100.0, alias="CRITICAL_THRESHOLD_PCT")
    nr_loss_multiplier: float = Field(default=1.35, alias="NR_LOSS_MULTIPLIER")
    data_source: DataSource = Field(default=DataSource.SAMPLE, alias="DATA_SOURCE")
    data_csv_path: str = Field(default="data/sample_campaigns.csv", alias="DATA_CSV_PATH")

    google_ads_developer_token: str = Field(default="", alias="GOOGLE_ADS_DEVELOPER_TOKEN")
    google_ads_client_id: str = Field(default="", alias="GOOGLE_ADS_CLIENT_ID")
    google_ads_client_secret: str = Field(default="", alias="GOOGLE_ADS_CLIENT_SECRET")
    google_ads_refresh_token: str = Field(default="", alias="GOOGLE_ADS_REFRESH_TOKEN")
    google_ads_customer_id: str = Field(default="", alias="GOOGLE_ADS_CUSTOMER_ID")
    google_ads_login_customer_id: str = Field(default="", alias="GOOGLE_ADS_LOGIN_CUSTOMER_ID")
    google_ads_lookback_days: int = Field(default=90, alias="GOOGLE_ADS_LOOKBACK_DAYS")

    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(default="openai/gpt-4o-mini", alias="OPENROUTER_MODEL")
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL")

    mtd_target_tolerance_pct: float = Field(default=5.0, alias="MTD_TARGET_TOLERANCE_PCT")
    daily_spend_vs_7day_tolerance_pct: float = Field(
        default=20.0, alias="DAILY_SPEND_VS_7DAY_TOLERANCE_PCT"
    )
    low_daily_spend_budget_pct: float = Field(default=50.0, alias="LOW_DAILY_SPEND_BUDGET_PCT")
    low_daily_spend_consecutive_days: int = Field(default=3, alias="LOW_DAILY_SPEND_CONSECUTIVE_DAYS")
    hourly_overspend_min_cost: float = Field(default=1000.0, alias="HOURLY_OVERSPEND_MIN_COST")
    hourly_overspend_vs_7day_pct: float = Field(default=50.0, alias="HOURLY_OVERSPEND_VS_7DAY_PCT")
    campaign_new_budget_deviation_pct: float = Field(
        default=50.0, alias="CAMPAIGN_NEW_BUDGET_DEVIATION_PCT"
    )
    campaign_new_budget_min_delta: float = Field(
        default=5000.0, alias="CAMPAIGN_NEW_BUDGET_MIN_DELTA"
    )
    campaign_zero_spend_hours: int = Field(default=6, alias="CAMPAIGN_ZERO_SPEND_HOURS")

    smtp_host: str = Field(default="", alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str = Field(default="", alias="SMTP_USER")
    smtp_password: str = Field(default="", alias="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")
    alert_from_email: str = Field(default="", alias="ALERT_FROM_EMAIL")
    alert_from_name: str = Field(
        default="Parul University (UG) - Sentinel AI",
        alias="ALERT_FROM_NAME",
    )
    email_subject_prefix: str = Field(
        default="[Parul University (UG)] - [Sentinel AI]",
        alias="EMAIL_SUBJECT_PREFIX",
    )
    alert_default_recipients: str = Field(
        default="kishorkp4912@gmail.com",
        alias="ALERT_DEFAULT_RECIPIENTS",
    )

    def model_post_init(self, __context: object) -> None:
        # Gmail app passwords are often pasted with spaces — strip them.
        object.__setattr__(self, "smtp_password", self.smtp_password.replace(" ", ""))

    @property
    def default_alert_recipients(self) -> list[str]:
        raw = self.alert_default_recipients.strip()
        if not raw:
            return []
        return [email.strip() for email in raw.split(",") if email.strip()]

    @property
    def openrouter_configured(self) -> bool:
        return bool(self.openrouter_api_key.strip())

    @property
    def smtp_configured(self) -> bool:
        return bool(self.smtp_host.strip() and self.smtp_user.strip() and self.smtp_password.strip())

    @property
    def alert_recipients_path(self) -> Path:
        return PROJECT_ROOT / "config" / "alert_recipients.yaml"

    @property
    def csv_path(self) -> Path:
        path = Path(self.data_csv_path)
        return path if path.is_absolute() else PROJECT_ROOT / path

    @property
    def google_ads_configured(self) -> bool:
        return all(
            [
                self.google_ads_developer_token,
                self.google_ads_client_id,
                self.google_ads_client_secret,
                self.google_ads_refresh_token,
            ]
        )

    def google_ads_missing_credentials(self) -> list[str]:
        required = {
            "GOOGLE_ADS_DEVELOPER_TOKEN": self.google_ads_developer_token,
            "GOOGLE_ADS_CLIENT_ID": self.google_ads_client_id,
            "GOOGLE_ADS_CLIENT_SECRET": self.google_ads_client_secret,
            "GOOGLE_ADS_REFRESH_TOKEN": self.google_ads_refresh_token,
        }
        return [name for name, value in required.items() if not value.strip()]


def get_settings() -> AppSettings:
    return AppSettings()
