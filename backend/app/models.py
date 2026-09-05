import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)

from .db import Base


def utcnow():
    return datetime.datetime.now(datetime.UTC)

class TimestampMixin:
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

class Merchant(Base, TimestampMixin):
    __tablename__ = 'merchants'
    merchant_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    active_twin_version = Column(Integer, default=1, nullable=False)

class MerchantTwinVersion(Base, TimestampMixin):
    __tablename__ = 'merchant_twin_versions'
    version_id = Column(String, primary_key=True)
    merchant_id = Column(String, ForeignKey('merchants.merchant_id'), nullable=False)
    version = Column(Integer, nullable=False)
    description = Column(String)

class Product(Base, TimestampMixin):
    __tablename__ = 'products'
    sku = Column(String, primary_key=True, index=True)
    merchant_id = Column(String, ForeignKey('merchants.merchant_id'), nullable=False)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)
    description = Column(Text)
    catalog_version = Column(Integer, default=1, nullable=False)

class ProductAttribute(Base, TimestampMixin):
    __tablename__ = 'product_attributes'
    attribute_id = Column(Integer, primary_key=True, autoincrement=True)
    sku = Column(String, ForeignKey('products.sku'), nullable=False)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)
    type = Column(String, nullable=False)

class InventorySnapshot(Base, TimestampMixin):
    __tablename__ = 'inventory_snapshots'
    inventory_id = Column(Integer, primary_key=True, autoincrement=True)
    sku = Column(String, ForeignKey('products.sku'), nullable=False)
    merchant_id = Column(String, ForeignKey('merchants.merchant_id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    version = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        CheckConstraint('quantity >= 0', name='chk_inventory_non_negative'),
    )

class PricingSnapshot(Base, TimestampMixin):
    __tablename__ = 'pricing_snapshots'
    pricing_id = Column(Integer, primary_key=True, autoincrement=True)
    sku = Column(String, ForeignKey('products.sku'), nullable=False)
    merchant_id = Column(String, ForeignKey('merchants.merchant_id'), nullable=False)
    price_paise = Column(Integer, nullable=False)
    cost_paise = Column(Integer, nullable=False)
    currency = Column(String, default="INR", nullable=False)
    version = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        CheckConstraint('price_paise >= 0', name='chk_price_non_negative'),
        CheckConstraint('cost_paise >= 0', name='chk_cost_non_negative'),
    )

class MerchantPolicy(Base, TimestampMixin):
    __tablename__ = 'merchant_policies'
    policy_id = Column(Integer, primary_key=True, autoincrement=True)
    merchant_id = Column(String, ForeignKey('merchants.merchant_id'), nullable=False)
    policy_type = Column(String, nullable=False)
    policy_data = Column(JSON, nullable=False)
    version = Column(Integer, nullable=False, default=1)

class BuyerProfile(Base, TimestampMixin):
    __tablename__ = 'buyer_profiles'
    buyer_id = Column(String, primary_key=True, index=True)
    persona = Column(String, nullable=False)
    autonomy_level = Column(String, nullable=False)

class BuyerIntent(Base, TimestampMixin):
    __tablename__ = 'buyer_intents'
    intent_id = Column(String, primary_key=True, index=True)
    buyer_id = Column(String, ForeignKey('buyer_profiles.buyer_id'), nullable=False)
    raw_intent = Column(Text, nullable=False)
    hard_constraints = Column(JSON)
    soft_preferences = Column(JSON)
    budget_paise = Column(Integer)
    expected_valid_sku_set = Column(JSON)
    seed = Column(Integer, nullable=False)

class Experiment(Base, TimestampMixin):
    __tablename__ = 'experiments'
    experiment_id = Column(String, primary_key=True, index=True)
    merchant_version = Column(Integer, nullable=False)
    buyer_cohort_version = Column(String, nullable=False)
    chaos_profile = Column(String, nullable=False)
    seed = Column(Integer, nullable=False)

class ExperimentRun(Base, TimestampMixin):
    __tablename__ = 'experiment_runs'
    run_id = Column(String, primary_key=True, index=True)
    experiment_id = Column(String, ForeignKey('experiments.experiment_id'), nullable=False)
    started_at = Column(DateTime(timezone=True), default=utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, nullable=False)

class TransactionTrace(Base, TimestampMixin):
    __tablename__ = 'transaction_traces'
    trace_id = Column(String, primary_key=True, index=True)
    run_id = Column(String, ForeignKey('experiment_runs.run_id'), nullable=False)
    buyer_id = Column(String, ForeignKey('buyer_profiles.buyer_id'), nullable=False)
    final_classification = Column(String)
    final_amount_paise = Column(Integer)
    currency = Column(String, default="INR")

class TraceEvent(Base, TimestampMixin):
    __tablename__ = 'trace_events'
    event_id = Column(Integer, primary_key=True, autoincrement=True)
    trace_id = Column(String, ForeignKey('transaction_traces.trace_id'), nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)

class ChaosInjection(Base, TimestampMixin):
    __tablename__ = 'chaos_injections'
    chaos_id = Column(String, primary_key=True, index=True)
    experiment_id = Column(String, ForeignKey('experiments.experiment_id'), nullable=False)
    trace_id = Column(String, ForeignKey('transaction_traces.trace_id'), nullable=True)
    type = Column(String, nullable=False)
    target = Column(String, nullable=False)
    before_state = Column(JSON)
    mutated_state = Column(JSON)
    reversible_patch = Column(JSON)

class FailureCluster(Base, TimestampMixin):
    __tablename__ = 'failure_clusters'
    failure_id = Column(String, primary_key=True, index=True)
    taxonomy = Column(String, nullable=False)
    stage = Column(String, nullable=False)
    reason_code = Column(String, nullable=False)
    estimated_lost_value_paise = Column(Integer, default=0)
    supporting_trace_ids = Column(JSON)

class RepairProposal(Base, TimestampMixin):
    __tablename__ = 'repair_proposals'
    repair_id = Column(String, primary_key=True, index=True)
    failure_id = Column(String, ForeignKey('failure_clusters.failure_id'), nullable=False)
    repair_type = Column(String, nullable=False)
    proposed_patch = Column(JSON, nullable=False)
    confidence = Column(Integer)
    estimated_repair_cost_paise = Column(Integer)
    status = Column(String, nullable=False, default="proposed")
    before_metrics = Column(JSON)
    after_metrics = Column(JSON)

class ReplayResult(Base, TimestampMixin):
    __tablename__ = 'replay_results'
    replay_id = Column(String, primary_key=True, index=True)
    repair_id = Column(String, ForeignKey('repair_proposals.repair_id'), nullable=False)
    trace_id = Column(String, ForeignKey('transaction_traces.trace_id'), nullable=False)
    success = Column(Boolean, nullable=False)
    metrics_diff = Column(JSON)

class PaymentOperation(Base, TimestampMixin):
    __tablename__ = 'payment_operations'
    operation_id = Column(String, primary_key=True, index=True)
    trace_id = Column(String, ForeignKey('transaction_traces.trace_id'), nullable=False)
    amount_paise = Column(Integer, nullable=False)
    currency = Column(String, default="INR", nullable=False)
    state = Column(String, nullable=False)
    razorpay_order_id = Column(String)
    razorpay_payment_id = Column(String)
    razorpay_signature = Column(String)
    payment_operation_fingerprint = Column(String, unique=True, nullable=False)

    __table_args__ = (
        CheckConstraint('amount_paise >= 0', name='chk_payment_amount_non_negative'),
    )

class ProcessedWebhookEvent(Base, TimestampMixin):
    __tablename__ = 'processed_webhook_events'
    event_id = Column(Integer, primary_key=True, autoincrement=True)
    razorpay_event_id = Column(String, unique=True, nullable=False)
    event_type = Column(String, nullable=False)
    processed_state = Column(String, nullable=False)
