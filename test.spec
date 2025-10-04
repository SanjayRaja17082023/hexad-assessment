import { test, request, Response, expect, Page } from '@playwright/test';
import fs from 'fs';
 import { JSONPath } from 'jsonpath-plus'; 
 import { v4 as uuidv4 } from "uuid"; 
 import { multiremote } from "webdriverio"; 
 import path from 'path'; 
 import { promisify } from 'util';
  import xpath from "xpath"; 
 import { DOMParser } from "xmldom"; 
 import xmlFormatter from "xml-formatter";
import { exec } from 'child_process';

import axios, { AxiosError } from 'axios';

const execPromise = promisify(exec);

import vm from "vm";

import FormData from "form-data";

import https from 'https'; 

import pdfParse from 'pdf-parse';

  import { chromium } from 'playwright';
  

 interface TestDataProps {
  environmentVariables?: any[];
  globalVariables?: any[];
  testDataProfile?: any[];
  extractors?: any[];
}
  let testData: TestDataProps = {};
  const parseIfNumeric = (value: string): string | number => {
    if (/^\d+$/.test(value)) {
      return Number(value);
    }
    return value;
  };
  const handleEndIndex = (endValue: string, iterationValue: any): number => {
      const trimmedValue = endValue.toLowerCase().trim();
      if (/^\d+$/.test(trimmedValue)) {
        return Number(trimmedValue);
      }
      if (trimmedValue === 'end' && Array.isArray(iterationValue)) {
        return iterationValue.length;
      } else if( trimmedValue === 'end' && typeof iterationValue === 'string') {
    try{
         const parsedValue = JSON.parse(iterationValue);
          return parsedValue.length;
    }
    catch (error) {
      console.error('Error parsing iterationValue:', error);
      return 0;
    }  
}
      return 0;
  };

  function resolveGlobalVariablesInFunctionBody(
    functionBody: string,
    globalVariables: any[]
  ): string {
    // Regex to match $global.variableName
  const globalVarPattern = /\$global\.([^\s,)\]}]+)/g;
  
    // Replace all occurrences
    return functionBody.replace(globalVarPattern, (match, variableName) => {
      const found = globalVariables.find((v) => v.name === variableName);
      if (!found) return match; // If not found, keep as is
  
      if (found.type === "text") {
        return found.value !== undefined ? JSON.parse(found.value) : "";
      } else if (found.type === "function") {
        const nestedBody = found.value ? JSON.parse(found.value) : "";
        return resolveGlobalVariablesInFunctionBody(nestedBody, globalVariables);
      }
  
      return match;
    });
  }
  const handleTestData = ( variables: any[], name: string | number, iteration: any = undefined, index: number | undefined = undefined ) => {
  if (typeof name === 'number') {
    return name; // If name is a number, return it directly
  }

  if (typeof name === 'string' && name.startsWith('g:|') && name.endsWith('|')) {
    const variable = variables.find((variable) => variable.name === name.substring(3, name.length - 1));
    if(variable.type === 'text'){
      return variable?.value !== undefined ? variable.value : name;
    } else if(variable.type === 'function'){
      const rawFunctionBody = variable?.value ? JSON.parse(variable.value) : undefined;
      const functionBody = resolveGlobalVariablesInFunctionBody(rawFunctionBody, globalVariables);
      const script = '(function() {' + functionBody + '})()'
      // const script = '(async function() {' + functionBody + '})()'
      try {
    const sandbox = { 
      console: console,
      // fetch: global.fetch,
    };
    
    vm.createContext(sandbox);
    const result = vm.runInNewContext(script, sandbox, { timeout: 1000 });
    return result !== undefined && result !== null ? result : "";
  } catch (err) {
    console.error("Error executing user function in VM:", err);
    return undefined;
  }
    }
  } 
   else if(typeof name === 'string' && name.startsWith('i:|') && name.endsWith('|') && index !== undefined && Array.isArray(iteration) ) {
     return  extractIterationValue(name, iteration, index); 
  }
    else {
    return name;
  }
};
 const evaluateCondition = (
    value: any,
    comparisonValue: any,
    operator: string
  ): boolean => {
    switch (operator) {
      case "===":
        return value === comparisonValue ;
      case "!==":
        return value !== comparisonValue;
      case ">":
        return value > comparisonValue;
      case "<":
        return value < comparisonValue;
      case ">=":
        return value >= comparisonValue;
      case "<=":
        return value <= comparisonValue;
      default:
        throw new Error('Invalid operator:'+operator);
    }
  };
  const handleAPIConditional = (
    index:number,
    iterationValue: any,
    testdata: string,
  ): boolean => {
    const parsedTestData = JSON.parse(testdata)
     return evaluateCondition(
      parseIfNumeric(handleTestData(globalVariables, parsedTestData?.test_data_1.value, iterationValue, index)),
      parseIfNumeric(handleTestData(globalVariables, parsedTestData?.test_data["test-data"]?.value, iterationValue, index)),
      parsedTestData?.operator
    );
  };


export const compareImages = async (expectedImgPath: string, ActualImgPath: string, DiffImgPath: string): Promise<boolean> => {
  const { PNG } = await import('pngjs');
  const pixelmatch = (await import('pixelmatch')).default;

  const img1 = PNG.sync.read(fs.readFileSync(expectedImgPath));
  const img2 = PNG.sync.read(fs.readFileSync(ActualImgPath));
  const { width, height } = img1;
  const diff = new PNG({ width, height });

  const numDiffPixels = pixelmatch(img1.data, img2.data, diff.data, width, height ,{ threshold: 0.1, alpha:0.5 , includeAA: true });
    if (numDiffPixels > 0) {
    fs.writeFileSync(DiffImgPath, PNG.sync.write(diff));
  }

  return numDiffPixels === 0;
};


const findExtractorValue = (extractors: any, response: any, apiUUID: string) => {
  let resultExtraction = [] as any;
  try{
  if (response) {
    extractors.map(async (extractor: any) => {
      const result = JSONPath({ path: extractor.jsonPath, json: response });
      if (result.length > 0) {
        resultExtraction.push({
          ...extractor,
          result: result.length > 1 ? result : result[0],
        });

        if (extractor?.type === 'globalVariable' || ( extractor?.isGlobal ?? false)) {
          globalVariables = updateGlobalVariableValueByName(globalVariables, extractor.variableName, result.length > 1 ? result : result[0]);
        }
        if( extractor?.type === 'storeVariable') {
          storeVariables = storeVariableWithValue(storeVariables, extractor.variableName, result[0], apiUUID);
        }
      }
    });
  }
} catch (error) {
  console.error('JSONPath selection error for', error);
  }
  return resultExtraction.length > 0 ? resultExtraction : null;
};

const findSoapExtractorValue = async (extractors: any, response: any) => {
  const namespaceRegex = /xmlns:([a-zA-Z0-9]+)="([^"]+)"/g;
  const defaultNamespaceRegex = /xmlns="([^"]+)"/;
  const namespaces: any = {};
  let match;
  let responseText = await response.text();

  // Extract prefixed namespaces
  while ((match = namespaceRegex.exec(responseText)) !== null) {
    namespaces[match[1]] = match[2]; // { prefix: URI }
  }

  // Handle default namespace
  const defaultMatch = defaultNamespaceRegex.exec(responseText);
  if (defaultMatch) {
    namespaces["ns"] = defaultMatch[1]; // Assign a prefix "ns" for the default namespace
  }

  // Ensure the "soap" namespace is included
  if (!namespaces["soap"]) {
    namespaces["soap"] = "http://schemas.xmlsoap.org/soap/envelope/"; // Add SOAP namespace manually
  }

  // Parse XML
  const doc = new DOMParser().parseFromString(responseText);
  const select = xpath.useNamespaces(namespaces);

  let resultExtraction: any = [];

  if (responseText) {
    extractors.map((extractor: any) => {
      try {
        const nodes: any = select(extractor.jsonPath, doc);
        if (nodes.length > 0) {
          resultExtraction.push({
            ...extractor,
            result: nodes[0].nodeValue || nodes[0].textContent,
          });
        }
      } catch (error) {
        console.error('XPath selection error for', error);
      }
    });
  }

  return resultExtraction.length > 0 ? resultExtraction : null;
};

const verifyAssertions = async (assertions: any[], response: any) => {
 
  const data = await response.json();
  const status = await response.status();
  const headers = await response.headers();

  return assertions.map((assertion:any) => {
    try {
      let actualValue: any = null;
      let expectedValue: any = assertion.expectedValue;
      if (assertion.isGlobal) {
         const globalVariable = globalVariables.find((variable: any) => variable.name === assertion.expectedValue);
         if(globalVariable && globalVariable.value) {
          assertion.expectedValue = globalVariable.type === "text" ? globalVariable.value : executeGlobalVariableFunction(globalVariable);
         }
      }

      switch (assertion.type) {
        case 'jsonPath':
          if (!assertion.jsonPath) {
            console.warn('Missing JSONPath in assertion:', assertion);
            break;
          }
          const result = JSONPath({ path: assertion.jsonPath, json: data });
          actualValue = result?.[0] ?? result;
          break;

        case 'statusCode':
          actualValue = status;
          break;

        case 'header':
          if (!assertion.jsonPath) {
            console.warn('Missing header key in assertion:', assertion);
            break;
          }
          const headerKey = assertion.jsonPath.toLowerCase();
          actualValue =
            headers?.[headerKey] ??
            Object.entries(headers || {}).find(
              ([key]) => key.toLowerCase() === headerKey
            )?.[1];
          break;

        default:
          if (!assertion.jsonPath) {
            console.warn("Missing JSONPath in assertion:", assertion);
            break;
          }
          const results = JSONPath({ path: assertion.jsonPath, json: data });
          actualValue = results?.[0] ?? results;
      }

      // Convert expectedValue to number if numeric
      if (/^\d+$/.test(expectedValue)) {
        expectedValue = Number(expectedValue);
      }

      if (actualValue === expectedValue) {
        return {
          ...assertion,
          responseStatus: 'PASSED',
          actualValue,
        };
      } else {
        return {
          ...assertion,
          responseStatus: 'FAILED',
          actualValue,
        };
      }
    } catch (error: any) {
      console.error('Error evaluating assertion:', assertion, error.message);
      return {
        ...assertion,
        responseStatus: 'FAILED',
        actualValue: 'ERROR:' +error.message,
      };
    }
  });
};

const verifySoapAssertions = async (assertions: any, response: any) => {
  const namespaceRegex = /xmlns:([a-zA-Z0-9]+)="([^"]+)"/g; // Match namespace declarations
  const defaultNamespaceRegex = /xmlns="([^"]+)"/; // Default namespace
  const namespaces: Record<string, string> = {};
  let match;
  let responseText = await response.text();

  // Extract all prefixed namespaces
  while ((match = namespaceRegex.exec(responseText)) !== null) {
    namespaces[match[1]] = match[2]; // { prefix: URI }
  }

  // Handle default namespace (if present)
  const defaultMatch = defaultNamespaceRegex.exec(responseText);
  if (defaultMatch) {
    namespaces["ns"] = defaultMatch[1]; // Assign a prefix "ns" for the default namespace
  }

  // Parse XML response
  const doc = new DOMParser().parseFromString(responseText, "text/xml");
  const select = xpath.useNamespaces(namespaces);

  return assertions.map((assertion: any) => {
    try {
      // Execute XPath query
      const nodes: any = select(assertion.jsonPath, doc);
      const result = nodes.length ? nodes[0].textContent : null;

      if(assertion.isGlobal){
      assertion.expectedValue = globalVariables.find((variable: any) => variable.name === assertion.expectedValue)?.value;
    }

      return {
        ...assertion,
        responseStatus: result === assertion.expectedValue.toString() ? "PASSED" : "FAILED",
        actualValue: result,
      };
    } catch (error: any) {
      return {
        ...assertion,
        responseStatus: "ERROR",
        errorMessage: error.message,
      };
    }
  });
};

const updateGlobalVariableValueByName = (
  variables: any[],
  name: string,
  newValue: string
): any[] => {
  const updatedVariables = variables.map((variable) => {
    if (variable.name === name) {
      return {
        ...variable,
        value: newValue,
      };
    }
    return variable;
  });

  return updatedVariables;
};

let storedVariables: any[] = []; // Array to store variables

const storeVariableWithValue = (variables: any[], name: string, newValue: string, apiUUID: string, referenceUUID?: string) => {
  const updatedVariables = variables.map((variable) => {
    if (variable.name === name) {
      const updatedVariable = {
        ...variable,
        value: newValue,
        fullContextReferenceUUID: apiUUID, // Add the apiUUID to the variable
        reference_uuid: referenceUUID ? referenceUUID : 'null', // Add the reference UUID if provided
      };
      storedVariables.push(updatedVariable); // Store the updated variable in the array
      return updatedVariable;
    }
    return variable;
  });
  return updatedVariables;
};

const convertKeyValueToObject = (
  keyPairs: { keyItem: string; valueItem: any }[]
) => {
  return keyPairs.reduce((data, pair) => {
    const key = pair.keyItem;
    const value = pair.valueItem;

    if (key === '') return data;
    return {
      ...data,
      [key]: value,
    };
  }, {});
};


//  function to executr thr global variable function
const executeGlobalVariableFunction = (
  variable: any,

) => {
  if (variable?.type !== 'function' || !variable?.value) {
    return undefined;
  }

  try {
    const rawFunctionBody = JSON.parse(variable.value);
    const functionBody = resolveGlobalVariablesInFunctionBody(rawFunctionBody, globalVariables);

    // Wrap inside an IIFE
 const script = '(function() {' + functionBody + '})()'
//  if You need async support
      // const script = '(async function() {' + functionBody + '})()'



    const sandbox = {
      console,
      // Add more safe utilities if required
      // fetch: global.fetch, etc.
    };

    vm.createContext(sandbox); // prepare the context

    const result = vm.runInNewContext(script, sandbox, { timeout: 1000 });

    return result ?? "";
  } catch (err) {
    console.error("Error executing user function in VM:", err);
    return undefined;
  }
};

function isNonEmptyData(data: any): boolean {
  if (data === null || data === undefined) return false;

  if (typeof data === "string") return data.trim().length > 0;

  if (Array.isArray(data)) return data.length > 0;

  if (typeof data === "object") return Object.keys(data).length > 0;

  return true; // for any other types
}

export const extractIterationValue = (
  expression: string,
  item: any,
  index: number
): any => {
  // Match i:|item.<jsonpath>|
  const pathMatch = expression.match(/^i:\|item.([^|]+)\|$/);
  if (pathMatch) {
    const jsonPath = pathMatch[1];

    try {
      const result = JSONPath({ path: jsonPath, json: item[index] });

      if (
        result === undefined ||
        result === null ||
        (Array.isArray(result) && result.length === 0)
      ) {
        return undefined;
      }

      return Array.isArray(result) && result.length === 1 ? result[0] : result;
    } catch (err) {
      console.error("Error parsing JSONPath from expression:", expression);
      return undefined;
    }
  }

  // Match full item access: i:|item|
  if (expression.trim() === "i:|item|") {
    return item[index];
  }

  // Not a match — return raw input
  return expression;
};

const updateURLWithIterationValue = (
  url: string,
  array: any[],
  index: number
): any => {
  return url
    // Handle i:|item.jsonpath|
    .replace(/i:\|item\.([^|]+)\|/g, (match, jsonPath) => {
      try {
        const result = JSONPath({ path: jsonPath, json: array[index] });

        if (result === undefined || result === null || (Array.isArray(result) && result.length === 0)) {
          return match;
        }

        const value = Array.isArray(result) && result.length === 1 ? result[0] : result;

        // Handle proper formatting
        if (Array.isArray(value)) return JSON.stringify(value);
        if (typeof value === 'object') return JSON.stringify(value);
        return String(value);
      } catch (err) {
        console.error('JSONPath error at expression:', err);
        return match;
      }
    })

    // Handle i:|item|
    .replace(/i:\|item\|/g, () => {
      const value = array[index];
      return typeof value === 'object' ? JSON.stringify(value) : String(value);
    });
};


const updateBodyWithIterationValue = (
  body: any,
  iterationsValue: any[],
  index: number
): any => {
if ( !Array.isArray(iterationsValue) || typeof index !== 'number' || index < 0 || index >= iterationsValue.length || iterationsValue[index] === undefined || iterationsValue[index] === null ) {
  return body;
}

  const currentItem = iterationsValue[index];

  const replaceIterationPlaceholders = (value: string): string => {
    return value.replace(/i:\|item.([^|]+)\|/g, (match, jsonPath) => {
        try {
          const result = JSONPath({ path: jsonPath, json: currentItem });

          if (
            result === undefined ||
            result === null ||
            (Array.isArray(result) && result.length === 0)
          ) {
            return match;
          }

          const value =
            Array.isArray(result) && result.length === 1 ? result[0] : result;

          // Handle proper formatting
          if (Array.isArray(value)) return JSON.stringify(value);
          if (typeof value === "object") return JSON.stringify(value);
          return String(value);
        } catch (err) {
          console.error("JSONPath error at expression:", err);
          return match;
        }
      })

      // Handle i:|item|
      .replace(/i:\|item\|/g, () => {
        const value = currentItem;
        return typeof value === "object"
          ? JSON.stringify(value)
          : String(value);
      })
  };

  const deepReplace = (input: any): any => {
    if (typeof input === "string") {
      return replaceIterationPlaceholders(input);
    }

    if (Array.isArray(input)) {
      return input.map((item) => deepReplace(item));
    }

    if (typeof input === "object" && input !== null) {
      const newObj: any = {};
      for (const [key, val] of Object.entries(input)) {
        newObj[key] = deepReplace(val);
      }
      return newObj;
    }

    return input; // primitive values
  };

  return deepReplace(body);
};

const replacePlaceholders = (obj: any, match: string, replacementResult: any): any => {
  if (typeof obj === 'string') {
    if (typeof replacementResult === 'number' || typeof replacementResult === 'boolean') {
      // If the whole string is the match, replace with number/boolean directly
      return obj === match ? replacementResult : obj;
    } else if (typeof replacementResult === 'string') {
      // Replace occurrences of match in the string
      return obj.replace(match, replacementResult);
    }
     else if(typeof replacementResult === 'object' && replacementResult !== null) {
      // If the replacementResult is an object, replace the match with its stringified version
      return obj.replace(match, JSON.stringify(replacementResult));
    }  
  } else if (Array.isArray(obj)) {
    return obj.map(item => replacePlaceholders(item, match, replacementResult));
  } else if (typeof obj === 'object' && obj !== null) {
    const updatedObj: any = {};
    for (const key in obj) {
      updatedObj[key] = replacePlaceholders(obj[key], match, replacementResult);
    }
    return updatedObj;
  }
  // Return as is if not string/array/object
  return obj;
}

const replaceVariablesWithExtractorValues = (
  bodyInfo: any,
  structureData: any[]
): any => {

  if (Array.isArray(bodyInfo)) {
    return bodyInfo.map((item) => replaceVariablesWithExtractorValues(item, structureData));
  }

  if (typeof bodyInfo === "object" && bodyInfo !== null) {
    const data: any = { ...bodyInfo };

    for (const [key, value] of Object.entries(data)) {
      if (typeof value === "string" && structureData) {
        const match = value.match(/\${(.*?)}/g);

        if (match) {
          match.forEach((matchStr) => {
            const variableName = matchStr.substring(2, matchStr.length - 1);

            const replacement = structureData.find(
              (extractor: any) => extractor.variableName === variableName
            );

            if (replacement) {
              testData = {
                ...testData,
                extractors: [...(testData.extractors ?? []), replacement],
              };
              const replacementResult = replacement.result;
              data[key] = replacePlaceholders(data[key], matchStr, replacementResult);
            }
          });
        }
      } else if (typeof value === "object" && value !== null) {
        // Deep recursion for nested objects or arrays
        data[key] = replaceVariablesWithExtractorValues(value, structureData);
      }
    }

    return data;
  }

  // Primitive values (number, boolean, etc.)
  return bodyInfo;
};


const replaceVariablesInXML = (data: any, structureData: any[]): any => {
  // Check if the data is an object with body containing raw XML data
  if (data.body && data.body[0]?.rawValue) {
    // Check if the rawValue contains XML format
    const xmlString = data.body[0].rawValue;

    // Replace variables in the XML string
    const modifiedXML = xmlString.replace(
      /\${(.*?)}/g, 
      (match: any, variableName: string) => {
        const replacement = structureData.find(
          (extractor: any) => extractor.variableName === variableName // Find the matching variableName
        );
        replacement && (testData = {...testData, extractors: [...(testData.extractors || []), replacement]});
        return replacement ? replacement.result : match; // Replace with result or keep original
      }
    );

    // Return the modified structure with updated XML
    return {
      ...data,
      body: [
        {
          ...data.body[0],
          rawValue: modifiedXML, // Replace raw XML data
        },
      ],
    };
  }

  // If no XML is found, return the data as is
  return data;
};

const replaceEnvironmentalVariablesInXML = (xmlString: string, environmentVariables: any) => {
    return xmlString.replace(/${{(.*?)}}/g, (match, variableName) => {
      const replacement = environmentVariables.find((extractor: any) => extractor.name === variableName);
      replacement && (testData = {...testData, environmentVariables: [...(testData.environmentVariables || []), replacement]});
      return replacement ? replacement.value : match; // Keep original if no replacement found
    });
  };

  const replaceGlobalVariablesVariablesInXML = (xmlString: string, globalVariables: any[]) => {
    return xmlString.replace(/g:|([^|]*)|/g, (match, variableName) => {
      const replacement = globalVariables.find((extractor: any) => extractor.name === variableName);
      replacement && (testData = {...testData, globalVariables: [...(testData.globalVariables || []), replacement]});
      return replacement ? replacement.value : match; // Keep original if no replacement found
    });
  };

// double curly braces global variable names
const replaceVariablesWithGlobalValues = (data: any, environmentVariables: any): any => {
  if (typeof data === 'string') {
    const matches = data.match(/\${{(.*?)}}/g);
    let result = data;
    if (matches) {
      matches.forEach((match) => {
        const variableName = match.substring(3, match.length - 2);
        const replacement = environmentVariables.find(
          (extractor: any) => extractor.name === variableName
        );
        if (replacement) {
          testData = { ...testData, environmentVariables: [...(testData.environmentVariables || []), replacement] };
          result = result.replace(match, replacement.value);
        }
      });
    }
    return result;
  } else if (Array.isArray(data)) {
    return data.map((item: any) => replaceVariablesWithGlobalValues(item, environmentVariables));
  } else if (typeof data === 'object' && data !== null) {
    const newObj: any = {};
    for (const [key, value] of Object.entries(data)) {
      newObj[key] = replaceVariablesWithGlobalValues(value, environmentVariables);
    }
    return newObj;
  }
  return data;
};
    
    
    const replaceExtractorsValueWithURL = (url: string = '', structureData: any[]) => {
  // Replace variable values in URL
  let modifiedUrl = url;
  const matches = url.match(/\${(.*?)}/g);
  if (matches && Array.isArray(structureData)) {
    matches.forEach((match: any) => {
      const variableName = match.substring(2, match.length - 1); // Remove curly braces
      const matchValue = structureData.find(
        (extractor: any) => extractor.variableName === variableName
      );
      if (matchValue) {
        testData = {...testData, extractors: [...(testData.extractors || []), matchValue
        ]};
        modifiedUrl = modifiedUrl.replace(match, matchValue.result);
      }
    });
  }
  return modifiedUrl;
};

const replaceGlobalVariablesWithValue = (bodyInfo: any, globalVariables: any[]) => {
  for (const [key, value] of Object.entries(bodyInfo)) {
    if (typeof value === 'string' && globalVariables) {
      const matches = value.match(/g:\|([^|]*)\|/g); // Match global variable format (g:||)
      if (matches) {
        matches.forEach((match) => {
          const variableName = match.substring(3, match.length - 1); // Remove g:| and |
          const replacement = globalVariables.find(
            (variable: any) => variable.name === variableName
          );
          if (replacement) {
            testData = {...testData, globalVariables: [...(testData.globalVariables || []), replacement]};
             if(replacement?.type === 'function'){
              const functionResult = executeGlobalVariableFunction(replacement);
              bodyInfo[key] = value.replace(match, functionResult);
            }
            else{
               bodyInfo[key] = value.replace(match, replacement.value);
            }
          }
        });
      }
    } else if (typeof value === 'object' && globalVariables && value !== null) {
      replaceGlobalVariablesWithValue(value, globalVariables);
    }
  }
  return bodyInfo;
};
    
    const replaceEnv_Glo_VarValueWithURL = (url: string = '', environmentVariables: any[], globalVariables: any[]) => {
  let alteredUrl = url;
  const globalVariableMatch = url.match(/\${{(.*?)}}/g); // Match double curly braces
  if (globalVariableMatch && Array.isArray(environmentVariables)) {
    globalVariableMatch.forEach((match: any) => {
      const variableName = match.substring(3, match.length - 2); // Remove double curly braces
      const matchValue = environmentVariables.find(
        (extractor: any) => extractor.name === variableName
      );
      if (matchValue) {
        testData = {...testData, environmentVariables: [...(testData.environmentVariables || []), matchValue]};
        alteredUrl = alteredUrl.replace(match, matchValue.value);
      }
    });
  }
  const isGlobalVariable = url.match(/g:\|[^|]*\|/g); // Match the global variable format (g:||)
  if (isGlobalVariable && Array.isArray(globalVariables)) {
    const globalVariableMap = new Map(globalVariables.map((variable: any) => [variable.name, variable.value]));
    alteredUrl = url.replace(/g:\|([^|]*)\|/g, (match, variableName) => {
           const findedVariable = globalVariables.find(
        (variable: any) => variable.name === variableName
      );
      if (!findedVariable) return match; // If not found, keep as is

      if (findedVariable && findedVariable?.type === 'function') {
            const functionResult = executeGlobalVariableFunction(findedVariable); // Make sure this returns a string
            testData = {...testData, globalVariables: [...(testData.globalVariables || []), { name: variableName, value: functionResult }]};
            return functionResult ?? match;
          } else {
            testData = {...testData, globalVariables: [...(testData.globalVariables || []), { name: variableName, value: findedVariable.value }]};
            return (findedVariable&&findedVariable?.value) !== undefined ? findedVariable.value : match;

          }
    });
  }
  return alteredUrl;
};

const bodyOperations = async (body: any, executablePath?: string[]) => {
  let bodyData: any = {};
  if (body && body.length > 0) {
    if (body[0].type === 'none') {
      bodyData = {};
    } else if (
      body[0].type === 'form-data' ||
      body[0].type === 'multipart/form-data'
    ) {
      const formDataString = await multipartFormData(body[0].multipart_form_data, executablePath);
      bodyData = formDataString;
    } else if (
      body[0].type === 'x-www-form-urlencoded' ||
      body[0].type === 'application/x-www-form-urlencoded'
    ) {
      const formUrlEncodedString = toFormUrlEncoded(body[0].x_www_form_urlencoded);
      bodyData = formUrlEncodedString;
    } else if (
      body[0].type === 'raw' ||
      body[0].rawType === 'application/json' ||
      body[0].rawType === 'application/xml'
    ) {
      bodyData = body[0].rawValue;
    }
  }
  return bodyData;
};

const authOperation = (auth: any) => {
  let authData: any = {};
  if (auth.length > 0) {
    if (auth[0].type === 'Bearer Token') {
      authData = {
        Authorization: 'Bearer ' + auth[0].token,
      };
    } else if (auth[0].type === 'Basic Auth') {
      authData = {
        Authorization: 'Basic ' + btoa(auth[0].userName + ':' + auth[0].password),
      };
    } else if (auth[0].type === 'OAuth 2.0') {
      authData = {
           Authorization:auth[0].oAuthHeaderPrefix +' '+ auth[0].oAuthTokenSecret,
      };
    } else if (auth[0].type === 'No Auth') {
      authData = {};
    }
  }
  return authData;
}
export const toKeyValueObject = (arr: { key: string; value: string }[]) => {
  return arr.reduce((acc, curr) => {
    if (curr.key) acc[curr.key] = curr.value;
    return acc;
  }, {} as Record<string, string>);
}

export const toFormUrlEncoded = (arr: { key: string; value: string }[]) => {
  const obj = toKeyValueObject(arr);
  return new URLSearchParams(obj).toString();
}

export function replaceFilePathsFromArray(
  fields: { key: string; value: string; keyType: 'text' | 'file' }[],
  fullPaths: string[]
) {
  return fields.map((field) => {
    if (field.keyType === 'file') {
      const filename = path.basename(field.value);
      const matchedPath = fullPaths.find(p => path.basename(p) === filename);
      if (matchedPath) {
        return { ...field, value: matchedPath };
      }
    }
    return field;
  });
}

export async function multipartFormData(arr: { key: string; value: string; keyType: 'text' | 'file' }[], executablePath?: string[]) {
  const multipart: Record<string, any> = {};
  const fields = replaceFilePathsFromArray(arr,executablePath ?? []);

  for (const field of fields) {
    if (field.keyType === 'text') {
      // simple text field
      multipart[field.key] = field.value;
    } else if (field.keyType === 'file') {
      // read file into a buffer
      const filePath = field.value;
      const buffer = await fs.promises.readFile(filePath);
      multipart[field.key] = {
        name: path.basename(filePath),
        buffer,
        // optional: infer mimeType if you like
        mimeType: 'application/octet-stream',
      };
    }
  }

  return multipart;
}
 

async function attachVideo(testInfo: any, videoDir: any) {
                  if (testInfo) {
                    const videoFiles = fs.readdirSync(videoDir).filter((file: any) => file.endsWith('.webm'));
                    if (videoFiles.length > 0) {
                      const videoPath = path.join(videoDir, videoFiles[0]);
                      await testInfo.attach('video', { path: videoPath, contentType: 'video/webm' });
                    }
                  }
                }
const downloadFilesAndSave = async (urls:string[] , folderPath:string ,serverRootPath:string) => {
  try {
    const apiContext = await request.newContext(); // Use Playwright's APIRequestContext

    // Ensure the folder exists (Sync version)
     if (!fs.existsSync(folderPath)) {
      fs.mkdirSync(folderPath, { recursive: true });
    }
     urls = urls.map((url) => {
      // Replace the URL with the local server path
      const modifiedUrl = url.replace('/\/g', '/');
      
      return serverRootPath + (modifiedUrl.startsWith('/') ? modifiedUrl : '/' + modifiedUrl)
    });
    console.log('Modified URLs:', urls);
    for (const url of urls) {
      const fileName = path.basename(url); // Extract file name from URL
      const filePath = path.join(folderPath, fileName);

      // Check if file already exists
      if (fs.existsSync(filePath)) {
        console.log(filePath);
        continue; // Skip downloading
      }

      console.log(url);

      const response = await apiContext.get(url);
      if (!response.ok()) {
        console.error(response.status());
        continue;
      }

      const buffer = await response.body();

      // Save file (Callback-based method)
      fs.writeFile(filePath, buffer, (err) => {
        if (err) {
          console.error(err);
        } else {
          console.log(filePath);
        }
      });
    }

  } catch (error) {
    console.error('Error downloading files:', error);
    throw error;
  }
};
const searchTextInPdf = async (
  input: string,
  searchText: string
): Promise<boolean> => {
  if (!input || !searchText) {
    console.log("Please provide a PDF file path/URL and text to search.");
    return false;
  }

  try {
    let fileBuffer;

    // Check if the input is a URL or a local file path
    if (input.startsWith('http://') || input.startsWith('https://')) {
      const response = await axios.get(input, { responseType: 'arraybuffer' });
      fileBuffer = response.data; // Buffer from URL
    } else {
    fileBuffer = fs.readFileSync(input); // Buffer from local file
    }

    const pdfData = await pdfParse(fileBuffer); // Extract text from the PDF
    const text = pdfData.text.toLowerCase(); // Normalize extracted text
    const normalizedSearchText = searchText.toLowerCase(); // Normalize search term

    const found = text.includes(normalizedSearchText); // Check if the text contains the search term
    return found;
  } catch (error) {
    console.error("Error reading PDF:", error);
    return false;
  }
};

test.beforeAll(async () => {
  
const fileurls : string [] = [];

  const folderPath = path.join(__dirname, 'uploads'); // Replace with your desired folder path

  await downloadFilesAndSave(fileurls, folderPath ,'https://teresa.ardianet.net:6443');
});

let globalVariables: any[] = [
  {
    "uuid": "ea39f9d5-0f31-44bb-8e59-9d42abb3b4e0",
    "application_uuid": "8E5CD34F-BA88-4905-93CD-499027615B91",
    "name": "Policynumber",
    "value": "Test",
    "created_on": "2025-05-28T12:21:28.937Z",
    "created_by": "Gurumoorthi Ganesan",
    "modified_on": "2025-05-28T12:21:28.937Z",
    "modified_by": "Gurumoorthi Ganesan",
    "type": "text"
  },
  {
    "uuid": "eead2725-58b0-40a4-925d-48937a673034",
    "application_uuid": "8E5CD34F-BA88-4905-93CD-499027615B91",
    "name": "Claim_Number",
    "value": "test",
    "created_on": "2025-06-03T11:49:44.307Z",
    "created_by": "Aravindan Kumaran",
    "modified_on": "2025-06-03T11:49:44.307Z",
    "modified_by": "Aravindan Kumaran",
    "type": "text"
  }
];

const environmentVariables: any[] = [
  {
    "uuid": "89ed687e-7743-4448-8423-b95451979084",
    "application_uuid": "8E5CD34F-BA88-4905-93CD-499027615B91",
    "name": "USERNAME",
    "value": "EXP",
    "created_on": "2025-09-03T04:09:26.710Z",
    "created_by": "Karthick Sakthivel",
    "modified_on": "2025-09-03T04:09:26.710Z",
    "modified_by": "Karthick Sakthivel"
  },
  {
    "uuid": "96b92a81-e4a2-4239-80c1-688f66596326",
    "application_uuid": "8E5CD34F-BA88-4905-93CD-499027615B91",
    "name": "PASSWORD",
    "value": "PASS",
    "created_on": "2025-09-03T04:09:40.743Z",
    "created_by": "Karthick Sakthivel",
    "modified_on": "2025-09-03T04:09:40.743Z",
    "modified_by": "Karthick Sakthivel"
  }
] 

let storeVariables: any[] = [];


 test('5f8cdeb8-b73f-4f71-af6f-41efb46ad57f', async ({browser}) => {

      const contextOptions = {
      viewport: null,
       deviceScaleFactor:undefined,
        recordVideo: {
          dir: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/videos/5f8cdeb8-b73f-4f71-af6f-41efb46ad57f',
        },
        headless: false,
        timeout: 30000,
      };
      const context = await browser.newContext(contextOptions);
      const page = await context.newPage();
         const pages: { [key: string]: Page } = {};
    
try { 
 await test.step("7283b74a-3cc2-4d35-aea6-83c2145ba709", async () => {
  

   pages['1394568662'] = page;
  
    await pages['1394568662'].goto(handleTestData(globalVariables,'http://10.192.190.131:8180/pc/PolicyCenter.do'));
    
    
    await pages['1394568662'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/7283b74a-3cc2-4d35-aea6-83c2145ba709.png' }); 
    
    
  });

  await pages['1394568662'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/7283b74a-3cc2-4d35-aea6-83c2145ba709.png' }); 
  } catch (error) {
   await pages['1394568662'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/7283b74a-3cc2-4d35-aea6-83c2145ba709.png' });
    throw error;
  }
   

try { 
 await test.step("98ae0d6b-99fe-4f0b-840b-7059d574cf7c", async () => {
  

  
  
    await pages['1394568662'].locator("//input[@id='Login:LoginScreen:LoginDV:username-inputEl']").fill(handleTestData(globalVariables,'exp_test'))
    
    
    await pages['1394568662'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/98ae0d6b-99fe-4f0b-840b-7059d574cf7c.png' }); 
    
    
  });

  await pages['1394568662'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/98ae0d6b-99fe-4f0b-840b-7059d574cf7c.png' }); 
  } catch (error) {
   await pages['1394568662'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/98ae0d6b-99fe-4f0b-840b-7059d574cf7c.png' });
    throw error;
  }
   

try { 
 await test.step("0381f5a6-47e4-4709-aa73-561a89fc84b3", async () => {
  

  
  
    await pages['1394568662'].locator("//input[@id='Login:LoginScreen:LoginDV:password-inputEl']").fill(handleTestData(globalVariables,'exp_test'))
    
    
    await pages['1394568662'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/0381f5a6-47e4-4709-aa73-561a89fc84b3.png' }); 
    
    
  });

  await pages['1394568662'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/0381f5a6-47e4-4709-aa73-561a89fc84b3.png' }); 
  } catch (error) {
   await pages['1394568662'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/0381f5a6-47e4-4709-aa73-561a89fc84b3.png' });
    throw error;
  }
   

try { 
 await test.step("b6e4d6f3-3c99-40be-8974-9f97dcc1eeed", async () => {
  

  
  
    await pages['1394568662'].locator("//span[@id='Login:LoginScreen:LoginDV:submit-btnInnerEl']").click()
    
    
    await pages['1394568662'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/b6e4d6f3-3c99-40be-8974-9f97dcc1eeed.png' }); 
    
    
  });

  await pages['1394568662'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/b6e4d6f3-3c99-40be-8974-9f97dcc1eeed.png' }); 
  } catch (error) {
   await pages['1394568662'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/b6e4d6f3-3c99-40be-8974-9f97dcc1eeed.png' });
    throw error;
  }
   

try { 
 await test.step("0b859bf8-852d-4471-bafd-0322f27bcfd1", async () => {
  

  
  
    await pages['MainTab'].waitForSelector(`
        xpath=//span[@id='DesktopActivities:DesktopActivitiesScreen:0']`
        , { state: 'visible' });
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['MainTab'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/0b859bf8-852d-4471-bafd-0322f27bcfd1.png' });
    throw error;
  }
   

try { 
 await test.step("aa73dfc4-eb29-4e7d-b095-6c3c3be2e039", async () => {
  

  
  
    await pages['1394568748'].locator("//span[@id='ContactFile:ContactFileMenuActions-btnEl']").click()
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568748'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/aa73dfc4-eb29-4e7d-b095-6c3c3be2e039.png' });
    throw error;
  }
   

try { 
 await test.step("04194068-1b4a-4333-835d-e28494ca520e", async () => {
  

  
  
    await pages['1394568748'].locator("//span[@id='Desktop:DesktopMenuActions:DesktopMenuActions_Create:DesktopMenuActions_NewAccount-textEl']").click()
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568748'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/04194068-1b4a-4333-835d-e28494ca520e.png' });
    throw error;
  }
   

try { 
 await test.step("edebffac-d601-4303-85da-b6e3ae66f878", async () => {
  

  
  
    await pages['1394568748'].locator("//a[@id='NewAccount:NewAccountScreen:NewAccountSearchDV:SearchAndResetInputSet:SearchLinksInputSet:Search']").click()
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568748'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/edebffac-d601-4303-85da-b6e3ae66f878.png' });
    throw error;
  }
   

try { 
 await test.step("1d6d6f03-8ec1-4cf9-9e01-b20eab8b0283", async () => {
  

  
  
    await pages['1394568748'].locator("//input[@id='NewAccount:NewAccountScreen:NewAccountSearchDV:GlobalPersonNameInputSet:FirstName-inputEl']").fill(handleTestData(globalVariables,'HAri'))
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568748'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/1d6d6f03-8ec1-4cf9-9e01-b20eab8b0283.png' });
    throw error;
  }
   

try { 
 await test.step("5c09ac83-aa17-4b45-b662-f2c86d458b31", async () => {
  

  
  
    await pages['1394568748'].keyboard.press('Tab');
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568748'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/5c09ac83-aa17-4b45-b662-f2c86d458b31.png' });
    throw error;
  }
   

try { 
 await test.step("1c451e22-3601-4708-b0e4-e21ea6f57714", async () => {
  

  
  
    await pages['1394568748'].locator("//input[@id='NewAccount:NewAccountScreen:NewAccountSearchDV:GlobalPersonNameInputSet:LastName-inputEl']").fill(handleTestData(globalVariables,'test'))
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568748'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/1c451e22-3601-4708-b0e4-e21ea6f57714.png' });
    throw error;
  }
   

try { 
 await test.step("1ebb4237-99a5-4849-b22b-20d919706780", async () => {
  

  
  
    await pages['1394568748'].locator("3Keypress").keyboard.press('Enter')
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568748'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/1ebb4237-99a5-4849-b22b-20d919706780.png' });
    throw error;
  }
   

try { 
 await test.step("9a7b9921-f851-46ea-a9d1-2d1c4afb1ae6", async () => {
  

  
  
    await pages['1394568748'].locator("//span[@id='NewAccount:NewAccountScreen:NewAccountButton-btnInnerEl']").click()
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568748'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/9a7b9921-f851-46ea-a9d1-2d1c4afb1ae6.png' });
    throw error;
  }
   

try { 
 await test.step("b6ec82c0-bec6-42fa-98fa-b192ad8e1658", async () => {
  

  
  
    await pages['1394568748'].locator("//span[@id='NewAccount:NewAccountScreen:NewAccountButton:NewAccount_Person-textEl']").click()
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568748'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/b6ec82c0-bec6-42fa-98fa-b192ad8e1658.png' });
    throw error;
  }
   

try { 
 await test.step("0a367869-4e60-4d22-8f6f-67e25ef2c235", async () => {
  

  
  
    await pages['MainTab'].waitForSelector(`
        xpath=//input[@id='CreateAccount:CreateAccountScreen:CreateAccountDV:CreateAccountContactInputSet:GlobalPersonNameInputSet:FirstName-inputEl']`
        , { state: 'visible' });
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['MainTab'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/0a367869-4e60-4d22-8f6f-67e25ef2c235.png' });
    throw error;
  }
   

try { 
 await test.step("465671a9-ca69-4c7a-b867-702d76d6ffe1", async () => {
  

  
  
    await pages['1394568748'].locator("//input[@id='CreateAccount:CreateAccountScreen:CreateAccountDV:CreateAccountContactInputSet:GlobalPersonNameInputSet:FirstName-inputEl']").fill(handleTestData(globalVariables,'Hari'))
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568748'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/465671a9-ca69-4c7a-b867-702d76d6ffe1.png' });
    throw error;
  }
   

try { 
 await test.step("fe05f9c0-eb55-4767-bda1-5312eff32d28", async () => {
  

  
  
    await pages['1394568748'].keyboard.press('Tab');
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568748'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/fe05f9c0-eb55-4767-bda1-5312eff32d28.png' });
    throw error;
  }
   

try { 
 await test.step("0aa4bd98-2828-41a3-8526-26446c18cdc4", async () => {
  

  
  
    await pages['1394568748'].locator("//input[@id='CreateAccount:CreateAccountScreen:CreateAccountDV:CreateAccountContactInputSet:GlobalPersonNameInputSet:LastName-inputEl']").fill(handleTestData(globalVariables,'Test'))
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568748'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/0aa4bd98-2828-41a3-8526-26446c18cdc4.png' });
    throw error;
  }
   

try { 
 await test.step("e68eb19c-0d01-484f-9ea2-5aef3ea7a74e", async () => {
  

  
  
    await pages['1394568748'].keyboard.press('Tab');
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568748'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/e68eb19c-0d01-484f-9ea2-5aef3ea7a74e.png' });
    throw error;
  }
   

try { 
 await test.step("ecf378be-6f6c-4a41-991f-81dc3552547b", async () => {
  

  
  
    await pages['1394568751'].locator("//input[@id='CreateAccount:CreateAccountScreen:CreateAccountDV:CreateAccountContactInputSet:CellPhone:GlobalPhoneInputSet:NationalSubscriberNumber-inputEl']").fill(handleTestData(globalVariables,'556-664-4555'))
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568751'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/ecf378be-6f6c-4a41-991f-81dc3552547b.png' });
    throw error;
  }
   

try { 
 await test.step("13030ea4-fac9-455c-b50e-f6dceac1d115", async () => {
  

  
  
    await pages['1394568751'].keyboard.press('Tab');
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568751'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/13030ea4-fac9-455c-b50e-f6dceac1d115.png' });
    throw error;
  }
   

try { 
 await test.step("364059f3-0feb-4fa6-9403-c6398e9424a6", async () => {
  

  
  
    await pages['1394568751'].locator("//input[@id='CreateAccount:CreateAccountScreen:CreateAccountDV:AddressInputSet:globalAddressContainer:GlobalAddressInputSet:AddressLine1-inputEl']").fill(handleTestData(globalVariables,'25 Main street'))
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568751'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/364059f3-0feb-4fa6-9403-c6398e9424a6.png' });
    throw error;
  }
   

try { 
 await test.step("865bf3ed-59a3-4ad5-8baa-dfc0e6e9d407", async () => {
  

  
  
    await pages['1394568751'].keyboard.press('Tab');
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568751'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/865bf3ed-59a3-4ad5-8baa-dfc0e6e9d407.png' });
    throw error;
  }
   

try { 
 await test.step("87825374-ed52-4ae4-b485-e224797695bc", async () => {
  

  
  
    await pages['1394568751'].locator("//input[@id='CreateAccount:CreateAccountScreen:CreateAccountDV:AddressInputSet:globalAddressContainer:GlobalAddressInputSet:City-inputEl']").fill(handleTestData(globalVariables,'Dallas'))
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568751'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/87825374-ed52-4ae4-b485-e224797695bc.png' });
    throw error;
  }
   

try { 
 await test.step("7464af52-790e-4fcc-9765-ccbb1aeaaf6f", async () => {
  

  
  
    await pages['1394568751'].keyboard.press('Tab');
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568751'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/7464af52-790e-4fcc-9765-ccbb1aeaaf6f.png' });
    throw error;
  }
   

try { 
 await test.step("85baf7ef-dbba-4ed8-977a-1db6a9838842", async () => {
  

  
  
    await pages['1394568751'].locator("//input[@id='CreateAccount:CreateAccountScreen:CreateAccountDV:AddressInputSet:globalAddressContainer:GlobalAddressInputSet:State-inputEl']").fill(handleTestData(globalVariables,'Florida'))
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568751'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/85baf7ef-dbba-4ed8-977a-1db6a9838842.png' });
    throw error;
  }
   

try { 
 await test.step("c68b6ed6-29d4-4728-a231-555d359226f0", async () => {
  

  
  
    await pages['1394568751'].locator("//li[@id='ext-element-109']").selectOption({ value: handleTestData(globalVariables,'') });
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568751'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/c68b6ed6-29d4-4728-a231-555d359226f0.png' });
    throw error;
  }
   

try { 
 await test.step("63d9b4a1-7312-4835-8548-279449a95190", async () => {
  

  
  
    await pages['1394568751'].keyboard.press('Tab');
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568751'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/63d9b4a1-7312-4835-8548-279449a95190.png' });
    throw error;
  }
   

try { 
 await test.step("e6e35f39-2d02-4b21-810f-791587e2afb7", async () => {
  

  
  
    await pages['1394568751'].locator("//input[@id='CreateAccount:CreateAccountScreen:CreateAccountDV:AddressInputSet:globalAddressContainer:GlobalAddressInputSet:PostalCode-inputEl']").fill(handleTestData(globalVariables,'32614'))
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568751'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/e6e35f39-2d02-4b21-810f-791587e2afb7.png' });
    throw error;
  }
   

try { 
 await test.step("c0379877-e051-4f8a-a05a-b2b0054bf67e", async () => {
  

  
  
    await pages['1394568751'].locator("//li[@id='ext-element-114']").selectOption({ value: handleTestData(globalVariables,'') });
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568751'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/c0379877-e051-4f8a-a05a-b2b0054bf67e.png' });
    throw error;
  }
   

try { 
 await test.step("398975e4-73e9-40d0-a2b4-a9fbf9f4b18d", async () => {
  

  
  
    await pages['1394568751'].keyboard.press('Tab');
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568751'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/398975e4-73e9-40d0-a2b4-a9fbf9f4b18d.png' });
    throw error;
  }
   

try { 
 await test.step("8817c144-7903-4d55-822b-20849633c7dc", async () => {
  

  
  
    await pages['1394568751'].locator("//input[@id='CreateAccount:CreateAccountScreen:CreateAccountDV:ProducerSelectionInputSet:Producer-inputEl']").fill(handleTestData(globalVariables,'Enigma Fire & Casualty'))
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568751'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/8817c144-7903-4d55-822b-20849633c7dc.png' });
    throw error;
  }
   

try { 
 await test.step("4004e074-56b5-41e7-9f09-6927e1ea7027", async () => {
  

  
  
    await pages['1394568751'].locator("//div[@id='CreateAccount:CreateAccountScreen:CreateAccountDV:ProducerSelectionInputSet:Producer:SelectOrganization']").click()
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568751'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/4004e074-56b5-41e7-9f09-6927e1ea7027.png' });
    throw error;
  }
   

try { 
 await test.step("3ef796ec-79e9-4331-b96a-4c3026db5911", async () => {
  

  
  
    await pages['1394568751'].locator("//input[@id='OrganizationSearchPopup:OrganizationSearchPopupScreen:OrganizationSearchDV:GlobalContactNameInputSet:Name-inputEl']").fill(handleTestData(globalVariables,'Enigma Fire & Casualty'))
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568751'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/3ef796ec-79e9-4331-b96a-4c3026db5911.png' });
    throw error;
  }
   

try { 
 await test.step("90b3f34b-4dac-47cd-adfe-71997fe024c7", async () => {
  

  
  
    await pages['1394568751'].locator("//a[@id='OrganizationSearchPopup:OrganizationSearchPopupScreen:OrganizationSearchDV:SearchAndResetInputSet:SearchLinksInputSet:Search']").click()
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568751'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/90b3f34b-4dac-47cd-adfe-71997fe024c7.png' });
    throw error;
  }
   

try { 
 await test.step("19538682-2038-4e32-a7bd-b691b50fd739", async () => {
  

  
  
    await pages['1394568751'].locator("//a[@id='OrganizationSearchPopup:OrganizationSearchPopupScreen:OrganizationSearchResultsLV:0:_Select']").click()
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568751'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/19538682-2038-4e32-a7bd-b691b50fd739.png' });
    throw error;
  }
   

try { 
 await test.step("ba4f04ea-86bc-4075-9e54-af751c97417a", async () => {
  

  
  
    await pages['1394568751'].keyboard.press('Tab');
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568751'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/ba4f04ea-86bc-4075-9e54-af751c97417a.png' });
    throw error;
  }
   

try { 
 await test.step("5b54f6da-ac4b-4d5b-897d-db342e2a67a1", async () => {
  

  
  
    await pages['1394568751'].locator("//input[@id='CreateAccount:CreateAccountScreen:CreateAccountDV:ProducerSelectionInputSet:ProducerCode-inputEl']").fill(handleTestData(globalVariables,'INT-3 Internal Producer Code - 3'))
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568751'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/5b54f6da-ac4b-4d5b-897d-db342e2a67a1.png' });
    throw error;
  }
   

try { 
 await test.step("1d2ad32a-af66-476d-a53b-d0f529935e3d", async () => {
  

  
  
    await pages['1394568751'].locator("//li[@id='ext-element-241']").selectOption({ value: handleTestData(globalVariables,'') });
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568751'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/1d2ad32a-af66-476d-a53b-d0f529935e3d.png' });
    throw error;
  }
   

try { 
 await test.step("544796ea-27ca-4a35-9a63-1852a223fa80", async () => {
  

  
  
    await pages['1394568751'].locator("//span[@id='CreateAccount:CreateAccountScreen:Update-btnInnerEl']").click()
    
    
     
    
    
  });

   
  } catch (error) {
   await pages['1394568751'].screenshot({ path: 'tests/932AE89A-8D4A-4546-9530-EBD461836401/1757677981797/screenshots/544796ea-27ca-4a35-9a63-1852a223fa80.png' });
    throw error;
  }
   

      await context.close();
      // await browser.close();
    
 console.log(JSON.stringify({'5f8cdeb8-b73f-4f71-af6f-41efb46ad57f-updatedStoreVariables':storedVariables}));
 storedVariables = [];

  });
