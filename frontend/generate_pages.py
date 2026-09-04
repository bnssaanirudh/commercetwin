import os

pages = ['Experiments', 'Traces', 'RevenueLeak', 'Repairs', 'ChaosLab', 'Payments']

for page in pages:
    content = f"""import React from 'react';

const {page}: React.FC = () => {{
  return (
    <div>
      <div className="page-header">
        <h2 className="page-title">{page}</h2>
        <p className="page-subtitle">Manage your {page.lower()} data</p>
      </div>
      <div className="card">
        <p>This is the {page} view.</p>
      </div>
    </div>
  );
}};

export default {page};
"""
    with open(f'src/pages/{page}.tsx', 'w') as f:
        f.write(content)
