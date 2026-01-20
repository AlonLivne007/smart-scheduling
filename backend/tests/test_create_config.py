"""Test creating sample optimization configuration."""

from app.data.session import SessionLocal
from app.data.models.optimization_config_model import OptimizationConfigModel
from datetime import datetime

db = SessionLocal()

try:
    # Create a default optimization configuration
    default_config = OptimizationConfigModel(
        config_name="Default Balanced",
        weight_fairness=0.3,
        weight_preferences=0.4,
        weight_cost=0.1,
        weight_coverage=0.2,
        max_runtime_seconds=300,
        mip_gap=0.01,
        is_default=True
    )
    
    db.add(default_config)
    db.commit()
    db.refresh(default_config)
    
    print(f'✅ Created optimization config: {default_config.config_name}')
    print(f'   ID: {default_config.config_id}')
    print(f'   Weights: Fairness={default_config.weight_fairness}, Preferences={default_config.weight_preferences}')
    print(f'   Runtime limit: {default_config.max_runtime_seconds}s')
    print(f'   Is default: {default_config.is_default}')
    
    # Query it back
    configs = db.query(OptimizationConfigModel).all()
    print(f'\n📊 Total optimization configs in database: {len(configs)}')
    for cfg in configs:
        print(f'   - {cfg.config_name} (ID: {cfg.config_id})')
    
except Exception as e:
    db.rollback()
    print(f'❌ Error: {e}')
finally:
    db.close()
