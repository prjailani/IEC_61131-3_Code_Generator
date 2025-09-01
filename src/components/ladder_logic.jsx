import React, { useState, useEffect, useCallback } from 'react';

// JSON Schema Definition for Ladder Logic
const LADDER_JSON_SCHEMA = {
  program: {
    name: "string",
    description: "string",
    variables: [
      {
        name: "string",
        type: "BOOL | INT | REAL | TIME",
        initialValue: "any",
        description: "string"
      }
    ],
    rungs: [
      {
        id: "string",
        elements: [
          {
            type: "NO | NC | COIL | TIMER | COUNTER | COMPARE | MATH",
            variable: "string",
            label: "string", 
            position: { x: "number", y: "number" },
            parameters: {
              preset: "any",
              operation: "string",
              value: "any"
            },
            connections: {
              input: ["elementId"],
              output: ["elementId"]
            }
          }
        ]
      }
    ]
  }
};

// Generic Element Renderer Component
const ElementRenderer = ({ element, isActive, onElementClick }) => {
  const { type, label, position, parameters = {}, variable } = element;
  const activeColor = "#10b981";
  const inactiveColor = "#6b7280";
  const fillColor = isActive ? "#ecfdf5" : "white";
  const strokeColor = isActive ? activeColor : inactiveColor;

  const elementProps = {
    onClick: () => onElementClick?.(element),
    className: "cursor-pointer transition-all duration-300",
    style: { transform: `translate(${position.x}px, ${position.y}px)` }
  };

  const renderElement = () => {
    switch (type) {
      case 'NO':
        return (
          <g {...elementProps}>
            <rect 
              width="50" height="25" 
              fill={fillColor} stroke={strokeColor} strokeWidth="2"
              rx="2"
            />
            <line x1="12" y1="6" x2="12" y2="19" stroke={strokeColor} strokeWidth="2"/>
            <line x1="38" y1="6" x2="38" y2="19" stroke={strokeColor} strokeWidth="2"/>
            {isActive && <circle cx="25" cy="12.5" r="3" fill={activeColor} className="animate-pulse"/>}
            <text x="25" y="40" textAnchor="middle" className="text-xs font-mono" fill={strokeColor}>
              {label}
            </text>
          </g>
        );

      case 'NC':
        return (
          <g {...elementProps}>
            <rect 
              width="50" height="25" 
              fill={fillColor} stroke={strokeColor} strokeWidth="2"
              rx="2"
            />
            <line x1="12" y1="6" x2="12" y2="19" stroke={strokeColor} strokeWidth="2"/>
            <line x1="38" y1="6" x2="38" y2="19" stroke={strokeColor} strokeWidth="2"/>
            <line x1="8" y1="12.5" x2="42" y2="12.5" stroke="#ef4444" strokeWidth="2"/>
            {isActive && <circle cx="25" cy="12.5" r="3" fill="#ef4444" className="animate-pulse"/>}
            <text x="25" y="40" textAnchor="middle" className="text-xs font-mono" fill={strokeColor}>
              {label}
            </text>
          </g>
        );

      case 'COIL':
        return (
          <g {...elementProps}>
            <circle 
              cx="25" cy="12.5" r="18" 
              fill={fillColor} stroke={strokeColor} strokeWidth="2"
            />
            <path d="M15 8 Q25 4 35 8" fill="none" stroke={strokeColor} strokeWidth="1.5"/>
            <path d="M15 17 Q25 21 35 17" fill="none" stroke={strokeColor} strokeWidth="1.5"/>
            {isActive && (
              <>
                <circle cx="25" cy="12.5" r="22" fill="none" stroke={activeColor} strokeWidth="1" opacity="0.3" className="animate-pulse"/>
                <circle cx="25" cy="12.5" r="6" fill={activeColor} opacity="0.6" className="animate-pulse"/>
              </>
            )}
            <text x="25" y="40" textAnchor="middle" className="text-xs font-mono" fill={strokeColor}>
              {label}
            </text>
          </g>
        );

      case 'TIMER':
        return (
          <g {...elementProps}>
            <rect 
              width="70" height="35" 
              fill={fillColor} stroke={strokeColor} strokeWidth="2"
              rx="4"
            />
            <circle cx="20" cy="17.5" r="8" fill="none" stroke={strokeColor} strokeWidth="1.5"/>
            <line x1="20" y1="17.5" x2="25" y2="12.5" stroke={strokeColor} strokeWidth="1.5"/>
            <text x="52" y="15" className="text-xs font-bold" fill={strokeColor}>TON</text>
            <text x="52" y="27" className="text-xs font-mono" fill={strokeColor}>
              {parameters.preset || '1s'}
            </text>
            {isActive && <circle cx="20" cy="17.5" r="6" fill={activeColor} opacity="0.3" className="animate-spin"/>}
            <text x="35" y="50" textAnchor="middle" className="text-xs font-mono" fill={strokeColor}>
              {label}
            </text>
          </g>
        );

      case 'COUNTER':
        return (
          <g {...elementProps}>
            <rect 
              width="70" height="35" 
              fill={fillColor} stroke={strokeColor} strokeWidth="2"
              rx="4"
            />
            <text x="35" y="15" textAnchor="middle" className="text-xs font-bold" fill={strokeColor}>CTU</text>
            <text x="35" y="27" textAnchor="middle" className="text-xs font-mono" fill={strokeColor}>
              PV:{parameters.preset || '10'}
            </text>
            {isActive && (
              <rect x="5" y="5" width="60" height="25" fill={activeColor} opacity="0.1" rx="2" className="animate-pulse"/>
            )}
            <text x="35" y="50" textAnchor="middle" className="text-xs font-mono" fill={strokeColor}>
              {label}
            </text>
          </g>
        );

      case 'COMPARE':
        return (
          <g {...elementProps}>
            <rect 
              width="60" height="30" 
              fill={fillColor} stroke={strokeColor} strokeWidth="2"
              rx="4"
            />
            <text x="30" y="15" textAnchor="middle" className="text-xs font-bold" fill={strokeColor}>
              {parameters.operation || '>='}
            </text>
            <text x="30" y="25" textAnchor="middle" className="text-xs font-mono" fill={strokeColor}>
              {parameters.value || '0'}
            </text>
            <text x="30" y="45" textAnchor="middle" className="text-xs font-mono" fill={strokeColor}>
              {label}
            </text>
          </g>
        );

      case 'MATH':
        return (
          <g {...elementProps}>
            <rect 
              width="60" height="30" 
              fill={fillColor} stroke={strokeColor} strokeWidth="2"
              rx="4"
            />
            <text x="30" y="15" textAnchor="middle" className="text-xs font-bold" fill={strokeColor}>
              {parameters.operation || 'ADD'}
            </text>
            <text x="30" y="25" textAnchor="middle" className="text-xs font-mono" fill={strokeColor}>
              {parameters.operand || '1'}
            </text>
            <text x="30" y="45" textAnchor="middle" className="text-xs font-mono" fill={strokeColor}>
              {label}
            </text>
          </g>
        );

      default:
        return (
          <g {...elementProps}>
            <rect width="50" height="25" fill="red" stroke="red" strokeWidth="2" opacity="0.3"/>
            <text x="25" y="17" textAnchor="middle" className="text-xs" fill="red">ERROR</text>
          </g>
        );
    }
  };

  return renderElement();
};

// Wire/Connection Component
const Wire = ({ start, end, isActive }) => {
  const strokeColor = isActive ? "#10b981" : "#6b7280";
  const strokeWidth = isActive ? "3" : "2";
  
  return (
    <>
      <line
        x1={start.x} y1={start.y}
        x2={end.x} y2={end.y}
        stroke={strokeColor}
        strokeWidth={strokeWidth}
        className="transition-all duration-300"
      />
      {isActive && (
        <circle r="3" fill="#10b981" opacity="0.8">
          <animateMotion
            dur="2s"
            repeatCount="indefinite"
            path={`M${start.x},${start.y} L${end.x},${end.y}`}
          />
        </circle>
      )}
    </>
  );
};

// Logic Evaluator
class LogicEvaluator {
  constructor(variables = {}) {
    this.variables = { ...variables };
    this.timers = new Map();
    this.counters = new Map();
  }

  updateVariables(newVariables) {
    this.variables = { ...this.variables, ...newVariables };
  }

  evaluateElement(element, deltaTime = 1000) {
    const { type, variable, parameters = {} } = element;
    
    switch (type) {
      case 'NO':
        return Boolean(this.variables[variable]);
        
      case 'NC':
        return !Boolean(this.variables[variable]);
        
      case 'TIMER':
        if (!this.timers.has(variable)) {
          this.timers.set(variable, { elapsed: 0, done: false });
        }
        
        const timer = this.timers.get(variable);
        const preset = this.parseTime(parameters.preset || '1s');
        
        if (this.variables[variable + '_IN']) {
          timer.elapsed += deltaTime;
          timer.done = timer.elapsed >= preset;
        } else {
          timer.elapsed = 0;
          timer.done = false;
        }
        
        this.variables[variable + '_Q'] = timer.done;
        this.variables[variable + '_ET'] = timer.elapsed;
        return timer.done;
        
      case 'COUNTER':
        if (!this.counters.has(variable)) {
          this.counters.set(variable, { count: 0, done: false });
        }
        
        const counter = this.counters.get(variable);
        const preset_count = parseInt(parameters.preset || '10');
        
        if (this.variables[variable + '_CU'] && !this.variables[variable + '_CU_PREV']) {
          counter.count++;
        }
        
        if (this.variables[variable + '_R']) {
          counter.count = 0;
        }
        
        counter.done = counter.count >= preset_count;
        this.variables[variable + '_Q'] = counter.done;
        this.variables[variable + '_CV'] = counter.count;
        this.variables[variable + '_CU_PREV'] = this.variables[variable + '_CU'];
        
        return counter.done;
        
      case 'COMPARE':
        const leftValue = this.variables[variable + '_LEFT'] || 0;
        const rightValue = parameters.value || 0;
        const operation = parameters.operation || '>=';
        
        switch (operation) {
          case '>=': return leftValue >= rightValue;
          case '<=': return leftValue <= rightValue;
          case '==': return leftValue == rightValue;
          case '!=': return leftValue != rightValue;
          case '>': return leftValue > rightValue;
          case '<': return leftValue < rightValue;
          default: return false;
        }
        
      case 'MATH':
        const inputValue = this.variables[variable + '_IN'] || 0;
        const operand = parameters.operand || 1;
        const mathOp = parameters.operation || 'ADD';
        
        let result = inputValue;
        switch (mathOp) {
          case 'ADD': result = inputValue + operand; break;
          case 'SUB': result = inputValue - operand; break;
          case 'MUL': result = inputValue * operand; break;
          case 'DIV': result = operand !== 0 ? inputValue / operand : 0; break;
        }
        
        this.variables[variable] = result;
        return result !== 0;
        
      default:
        return false;
    }
  }

  evaluateRung(rung) {
    let rungResult = true;
    const inputElements = rung.elements.filter(el => 
      ['NO', 'NC', 'TIMER', 'COUNTER', 'COMPARE'].includes(el.type)
    );
    
    // Evaluate input elements in series (AND logic)
    for (const element of inputElements) {
      const elementResult = this.evaluateElement(element);
      rungResult = rungResult && elementResult;
    }
    
    // Update output elements
    const outputElements = rung.elements.filter(el => 
      ['COIL', 'MATH'].includes(el.type)
    );
    
    for (const element of outputElements) {
      if (element.type === 'COIL') {
        this.variables[element.variable] = rungResult;
      } else if (element.type === 'MATH') {
        if (rungResult) {
          this.evaluateElement(element);
        }
      }
    }
    
    return rungResult;
  }

  parseTime(timeStr) {
    const num = parseFloat(timeStr);
    if (timeStr.includes('ms')) return num;
    if (timeStr.includes('s')) return num * 1000;
    if (timeStr.includes('m')) return num * 60000;
    return num;
  }
}

// Main Generic Ladder Logic Component
const GenericLadderLogic = () => {
  const [program, setProgram] = useState(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [variables, setVariables] = useState({});
  const [activeRungs, setActiveRungs] = useState(new Set());
  const [evaluator, setEvaluator] = useState(null);
  const [simulationSpeed, setSimulationSpeed] = useState(1000);

  // Sample JSON data
  const samplePrograms = {
    nlp_example: {
  "name": "Traffic Light Control System",
  "description": "Automated traffic light with pedestrian crossing and emergency override",
  "variables": [
    { "name": "AUTO_MODE", "type": "BOOL", "initialValue": true, "description": "Automatic Mode Enable" },
    { "name": "PEDESTRIAN_BTN", "type": "BOOL", "initialValue": false, "description": "Pedestrian Crossing Button" },
    { "name": "EMERGENCY_OVERRIDE", "type": "BOOL", "initialValue": false, "description": "Emergency Override Signal" },
    { "name": "RED_LIGHT", "type": "BOOL", "initialValue": true, "description": "Red Light Output" },
    { "name": "YELLOW_LIGHT", "type": "BOOL", "initialValue": false, "description": "Yellow Light Output" },
    { "name": "GREEN_LIGHT", "type": "BOOL", "initialValue": false, "description": "Green Light Output" },
    { "name": "PEDESTRIAN_LIGHT", "type": "BOOL", "initialValue": false, "description": "Pedestrian Walk Light" },
    { "name": "GREEN_TIMER_IN", "type": "BOOL", "initialValue": false, "description": "Green Timer Input" },
    { "name": "GREEN_TIMER_Q", "type": "BOOL", "initialValue": false, "description": "Green Timer Done" },
    { "name": "YELLOW_TIMER_IN", "type": "BOOL", "initialValue": false, "description": "Yellow Timer Input" },
    { "name": "YELLOW_TIMER_Q", "type": "BOOL", "initialValue": false, "description": "Yellow Timer Done" },
    { "name": "PED_TIMER_IN", "type": "BOOL", "initialValue": false, "description": "Pedestrian Timer Input" },
    { "name": "PED_TIMER_Q", "type": "BOOL", "initialValue": false, "description": "Pedestrian Timer Done" }
  ],
  "rungs": [
    {
      "id": "green_light_control",
      "elements": [
        {
          "type": "NO",
          "variable": "AUTO_MODE",
          "label": "AUTO",
          "position": { "x": 0, "y": 0 },
          "parameters": {}
        },
        {
          "type": "NC",
          "variable": "PEDESTRIAN_BTN",
          "label": "NO_PED",
          "position": { "x": 100, "y": 0 },
          "parameters": {}
        },
        {
          "type": "NC",
          "variable": "EMERGENCY_OVERRIDE",
          "label": "NO_EMRG",
          "position": { "x": 200, "y": 0 },
          "parameters": {}
        },
        {
          "type": "COIL",
          "variable": "GREEN_TIMER_IN",
          "label": "GT_IN",
          "position": { "x": 300, "y": 0 },
          "parameters": {}
        }
      ]
    },
    {
      "id": "green_timer",
      "elements": [
        {
          "type": "NO",
          "variable": "GREEN_TIMER_IN",
          "label": "GT_IN",
          "position": { "x": 0, "y": 0 },
          "parameters": {}
        },
        {
          "type": "TIMER",
          "variable": "GREEN_TIMER",
          "label": "T_GREEN",
          "position": { "x": 100, "y": 0 },
          "parameters": { "preset": "30s" }
        }
      ]
    },
    {
      "id": "yellow_timer_start",
      "elements": [
        {
          "type": "NO",
          "variable": "GREEN_TIMER_Q",
          "label": "GT_DONE",
          "position": { "x": 0, "y": 0 },
          "parameters": {}
        },
        {
          "type": "COIL",
          "variable": "YELLOW_TIMER_IN",
          "label": "YT_IN",
          "position": { "x": 100, "y": 0 },
          "parameters": {}
        }
      ]
    },
    {
      "id": "yellow_timer",
      "elements": [
        {
          "type": "NO",
          "variable": "YELLOW_TIMER_IN",
          "label": "YT_IN",
          "position": { "x": 0, "y": 0 },
          "parameters": {}
        },
        {
          "type": "TIMER",
          "variable": "YELLOW_TIMER",
          "label": "T_YELLOW",
          "position": { "x": 100, "y": 0 },
          "parameters": { "preset": "5s" }
        }
      ]
    },
    {
      "id": "green_output",
      "elements": [
        {
          "type": "NO",
          "variable": "GREEN_TIMER_IN",
          "label": "GT_IN",
          "position": { "x": 0, "y": 0 },
          "parameters": {}
        },
        {
          "type": "NC",
          "variable": "GREEN_TIMER_Q",
          "label": "GT_RUN",
          "position": { "x": 100, "y": 0 },
          "parameters": {}
        },
        {
          "type": "COIL",
          "variable": "GREEN_LIGHT",
          "label": "GREEN",
          "position": { "x": 200, "y": 0 },
          "parameters": {}
        }
      ]
    },
    {
      "id": "yellow_output",
      "elements": [
        {
          "type": "NO",
          "variable": "YELLOW_TIMER_IN",
          "label": "YT_IN",
          "position": { "x": 0, "y": 0 },
          "parameters": {}
        },
        {
          "type": "NC",
          "variable": "YELLOW_TIMER_Q",
          "label": "YT_RUN",
          "position": { "x": 100, "y": 0 },
          "parameters": {}
        },
        {
          "type": "COIL",
          "variable": "YELLOW_LIGHT",
          "label": "YELLOW",
          "position": { "x": 200, "y": 0 },
          "parameters": {}
        }
      ]
    },
    {
      "id": "red_output",
      "elements": [
        {
          "type": "NC",
          "variable": "GREEN_LIGHT",
          "label": "NO_GREEN",
          "position": { "x": 0, "y": 0 },
          "parameters": {}
        },
        {
          "type": "NC",
          "variable": "YELLOW_LIGHT",
          "label": "NO_YELLOW",
          "position": { "x": 100, "y": 0 },
          "parameters": {}
        },
        {
          "type": "COIL",
          "variable": "RED_LIGHT",
          "label": "RED",
          "position": { "x": 200, "y": 0 },
          "parameters": {}
        }
      ]
    },
    {
      "id": "pedestrian_control",
      "elements": [
        {
          "type": "NO",
          "variable": "PEDESTRIAN_BTN",
          "label": "PED_BTN",
          "position": { "x": 0, "y": 0 },
          "parameters": {}
        },
        {
          "type": "NO",
          "variable": "RED_LIGHT",
          "label": "RED_ON",
          "position": { "x": 100, "y": 0 },
          "parameters": {}
        },
        {
          "type": "COIL",
          "variable": "PEDESTRIAN_LIGHT",
          "label": "PED_WALK",
          "position": { "x": 200, "y": 0 },
          "parameters": {}
        }
      ]
    }
  ]
}
  };

  const [currentProgramKey, setCurrentProgramKey] = useState('nlp_example');

  // Initialize program
  useEffect(() => {
    const selectedProgram = samplePrograms[currentProgramKey];
    if (selectedProgram) {
      setProgram(selectedProgram);
      
      // Initialize variables
      const initialVars = {};
      selectedProgram.variables.forEach(v => {
        initialVars[v.name] = v.initialValue;
      });
      setVariables(initialVars);
      setEvaluator(new LogicEvaluator(initialVars));
    }
  }, [currentProgramKey]);

  // Simulation loop
  useEffect(() => {
    let interval;
    if (isSimulating && program && evaluator) {
      interval = setInterval(() => {
        // Simulate some input changes
        const newVars = { ...variables };
        
        // Simple simulation logic - Enhanced for NLP example
        if (Math.random() > 0.85) {
          newVars.TIME_6PM = !newVars.TIME_6PM; // Simulate 6PM trigger
        }
        if (Math.random() > 0.9) {
          newVars.TIME_6AM = !newVars.TIME_6AM; // Simulate 6AM trigger
        }
        if (Math.random() > 0.7) {
          newVars.MANUAL_SW = !newVars.MANUAL_SW;
        }
        if (Math.random() > 0.8) {
          newVars.AUTO_TIMER = !newVars.AUTO_TIMER;
        }
        if (Math.random() > 0.9) {
          newVars.START_BTN = !newVars.START_BTN;
        }

        evaluator.updateVariables(newVars);
        
        // Evaluate all rungs
        const activeSet = new Set();
        program.rungs.forEach((rung, index) => {
          const isActive = evaluator.evaluateRung(rung);
          if (isActive) {
            activeSet.add(index);
          }
        });
        
        setActiveRungs(activeSet);
        setVariables({ ...evaluator.variables });
      }, simulationSpeed);
    }
    
    return () => clearInterval(interval);
  }, [isSimulating, program, evaluator, simulationSpeed, variables]);

  const toggleSimulation = () => {
    setIsSimulating(!isSimulating);
  };

  const loadCustomProgram = (jsonProgram) => {
    try {
      const parsedProgram = typeof jsonProgram === 'string' ? JSON.parse(jsonProgram) : jsonProgram;
      setProgram(parsedProgram);
      
      const initialVars = {};
      parsedProgram.variables?.forEach(v => {
        initialVars[v.name] = v.initialValue;
      });
      setVariables(initialVars);
      setEvaluator(new LogicEvaluator(initialVars));
    } catch (error) {
      alert('Invalid JSON format: ' + error.message);
    }
  };

  const renderRung = (rung, rungIndex) => {
    const rungY = rungIndex * 120 + 60;
    const startX = 100;
    
    return (
      <g key={rung.id}>
        {/* Left Power Rail Connection */}
        <Wire 
          start={{ x: 40, y: rungY }}
          end={{ x: startX, y: rungY }}
          isActive={activeRungs.has(rungIndex)}
        />
        
        {/* Elements */}
        {rung.elements.map((element, elemIndex) => {
          const elemX = startX + element.position.x;
          const elemY = rungY + element.position.y - 12.5;
          
          return (
            <g key={elemIndex}>
              <g transform={`translate(${elemX}, ${elemY})`}>
                <ElementRenderer
                  element={element}
                  isActive={activeRungs.has(rungIndex) && variables[element.variable]}
                />
              </g>
              
              {/* Connection to next element */}
              {elemIndex < rung.elements.length - 1 && (
                <Wire 
                  start={{ x: elemX + 50, y: rungY }}
                  end={{ x: startX + rung.elements[elemIndex + 1].position.x, y: rungY }}
                  isActive={activeRungs.has(rungIndex)}
                />
              )}
            </g>
          );
        })}
        
        {/* Right Power Rail Connection */}
        {rung.elements.length > 0 && (
          <Wire 
            start={{ 
              x: startX + rung.elements[rung.elements.length - 1].position.x + 50, 
              y: rungY 
            }}
            end={{ x: 750, y: rungY }}
            isActive={activeRungs.has(rungIndex)}
          />
        )}
        
        {/* Rung Number */}
        <rect 
          x="5" y={rungY - 15} width="30" height="30" 
          fill={activeRungs.has(rungIndex) ? "#10b981" : "#f3f4f6"}
          stroke={activeRungs.has(rungIndex) ? "#10b981" : "#d1d5db"}
          strokeWidth="2" rx="4"
        />
        <text 
          x="20" y={rungY + 5} textAnchor="middle"
          className="text-sm font-bold select-none"
          fill={activeRungs.has(rungIndex) ? "white" : "#6b7280"}
        >
          {rungIndex + 1}
        </text>
      </g>
    );
  };

  if (!program) {
    return <div className="p-6">Loading program...</div>;
  }

  return (
    <div className="p-6 bg-gradient-to-br from-slate-50 to-blue-50 rounded-xl shadow-2xl max-w-6xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-800 mb-2 flex items-center gap-3">
          <span className="w-3 h-8 bg-gradient-to-b from-blue-500 to-green-500 rounded"></span>
          Generic Ladder Logic System
        </h1>
        <p className="text-gray-600">{program.description}</p>
      </div>
      
      <div className="mb-6 flex flex-wrap gap-4 items-center">
        <select 
          value={currentProgramKey}
          onChange={(e) => setCurrentProgramKey(e.target.value)}
          className="px-4 py-2 border-2 border-gray-300 rounded-lg font-medium focus:border-blue-500"
        >
          <option value="nlp_example">NLP Example - Light & Pump</option>
          <option value="simple_lighting">Simple Lighting</option>
          <option value="motor_control">Motor Control</option>
        </select>
        
        <button
          onClick={toggleSimulation}
          className={`px-6 py-2 rounded-lg font-semibold transition-all ${
            isSimulating 
              ? 'bg-red-500 hover:bg-red-600 text-white' 
              : 'bg-green-500 hover:bg-green-600 text-white'
          }`}
        >
          {isSimulating ? '⏹ Stop' : '▶ Start'} Simulation
        </button>
        
        <input 
          type="range" 
          min="200" max="2000" step="200"
          value={simulationSpeed}
          onChange={(e) => setSimulationSpeed(Number(e.target.value))}
          className="w-32"
        />
        <span className="text-sm">{(2200 - simulationSpeed) / 200}x</span>
      </div>
      
      {/* SVG Diagram */}
      <div className="border-4 border-gray-300 rounded-xl p-6 bg-white shadow-inner">
        <svg 
          width="800" 
          height={program.rungs.length * 120 + 120}
          className="bg-gradient-to-b from-gray-50 to-white rounded-lg"
        >
          {/* Power Rails */}
          <rect x="35" y="30" width="10" height={program.rungs.length * 120 + 50} fill="#1f2937" rx="5"/>
          <rect x="745" y="30" width="10" height={program.rungs.length * 120 + 50} fill="#1f2937" rx="5"/>
          
          <text x="40" y="20" textAnchor="middle" className="text-lg font-bold" fill="#1f2937">L1</text>
          <text x="750" y="20" textAnchor="middle" className="text-lg font-bold" fill="#1f2937">L2</text>
          
          {/* Rungs */}
          {program.rungs.map((rung, index) => renderRung(rung, index))}
        </svg>
      </div>
      
      {/* Variable Monitor */}
      <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="p-6 bg-white rounded-xl shadow-lg">
          <h3 className="text-lg font-bold mb-4 text-gray-800">Variable Monitor</h3>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {program.variables.map(variable => (
              <div key={variable.name} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <span className="font-mono text-sm">{variable.name}</span>
                <span className={`px-2 py-1 rounded text-xs font-semibold ${
                  variables[variable.name] ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
                }`}>
                  {String(variables[variable.name])}
                </span>
              </div>
            ))}
          </div>
        </div>
        
        <div className="p-6 bg-white rounded-xl shadow-lg">
          <h3 className="text-lg font-bold mb-4 text-gray-800">JSON Schema</h3>
          <pre className="text-xs bg-gray-50 p-4 rounded overflow-x-auto">
{`{
  "name": "Program Name",
  "description": "Program Description",
  "variables": [
    {
      "name": "VAR_NAME",
      "type": "BOOL|INT|REAL|TIME",
      "initialValue": false,
      "description": "Variable Description"
    }
  ],
  "rungs": [
    {
      "id": "rung_1",
      "elements": [
        {
          "type": "NO|NC|COIL|TIMER|COUNTER|COMPARE|MATH",
          "variable": "VARIABLE_NAME",
          "label": "DISPLAY_LABEL",
          "position": { "x": 0, "y": 0 },
          "parameters": {
            "preset": "value",
            "operation": ">=|<=|==|ADD|SUB",
            "value": 100
          }
        }
      ]
    }
  ]
}`}
          </pre>
        </div>
      </div>
    </div>
  );
};

export default GenericLadderLogic;