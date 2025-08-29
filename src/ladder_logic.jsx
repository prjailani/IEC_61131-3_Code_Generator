import React from 'react';
import ReactFlow, { Background } from 'reactflow';
import 'reactflow/dist/style.css';

const elements = [
  { id: '1', type: 'input', data: { label: '[ TIME == 18:00 ]' }, position: { x: 50, y: 100 } },
  { id: '2', data: { label: '( Light )' }, position: { x: 250, y: 100 } },
  { id: 'e1-2', source: '1', target: '2', animated: true }
];

export default function LadderDiagram() {
  return (
    <div style={{ height: 400 }}>
      <ReactFlow nodes={elements} edges={[]} fitView>
        <Background />
      </ReactFlow>
 </div>
);
}