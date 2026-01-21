#!/usr/bin/env node

/**
 * taming-stan CLI
 *
 * All-in-one Claude Code enhancement: Graphiti memory, intelligent guards, and STAN.FLUX rules.
 *
 * Usage:
 *   npx taming-stan install   - Interactive service selection + install
 *   npx taming-stan uninstall - Remove all installed services
 *   npx taming-stan status    - Show installation status
 *
 * Installation is RELATIVE to current working directory:
 *   cd ~ && npx taming-stan install       -> ~/.claude/
 *   cd /project && npx taming-stan install -> /project/.claude/
 */

const fs = require('fs');
const path = require('path');
const inquirer = require('inquirer');

const PACKAGE_NAME = 'taming-stan';
const os = require('os');

// Get cwd safely
function getCwd() {
  try {
    return process.cwd();
  } catch (e) {
    return null;
  }
}

const CWD = getCwd();

// Target paths (relative to current working directory)
const CLAUDE_DIR = CWD ? path.join(CWD, '.claude') : null;
const HOOKS_DIR = CLAUDE_DIR ? path.join(CLAUDE_DIR, 'hooks', PACKAGE_NAME) : null;
const RULES_DIR = CLAUDE_DIR ? path.join(CLAUDE_DIR, 'rules', PACKAGE_NAME) : null;
const COMMANDS_DIR = CLAUDE_DIR ? path.join(CLAUDE_DIR, 'commands', PACKAGE_NAME) : null;
const SETTINGS_PATH = CLAUDE_DIR ? path.join(CLAUDE_DIR, 'settings.json') : null;
const STATE_PATH = CLAUDE_DIR ? path.join(CLAUDE_DIR, `${PACKAGE_NAME}-installation-state.json`) : null;

// Registry path - always in HOME (global list of all project installations)
const HOME_DIR = os.homedir();
const REGISTRY_PATH = path.join(HOME_DIR, '.claude', `${PACKAGE_NAME}-installation-registry.json`);

// Source paths (relative to package root)
const PACKAGE_ROOT = path.resolve(__dirname, '..');
const SOURCE_HOOKS_DIR = path.join(PACKAGE_ROOT, 'hooks');
const SOURCE_RULES_DIR = path.join(PACKAGE_ROOT, 'rules');
const SOURCE_COMMANDS_DIR = path.join(PACKAGE_ROOT, 'commands');
const SOURCE_LIB_DIR = path.join(PACKAGE_ROOT, 'lib');

// Service definitions
const SERVICES = {
  // === Graphiti (Memory) ===
  graphiti: {
    category: 'graphiti',
    name: 'Graphiti',
    description: 'Long-term memory with knowledge graph (Recommended)',
    hooks: {
      'session-start': ['graphiti-context-loader.py'],
      'user-prompt-submit': ['session-reminder.py', 'graphiti-knowledge-reminder.py'],
      'pre-tool-use': ['graphiti-guard.py', 'graphiti-first-guard.py'],
      'post-tool-use': ['graphiti-retry-guard.py']
    },
    preToolUseMatchers: {
      'graphiti-guard.py': ['mcp__graphiti.*', 'mcp__mcp-funnel__bridge_tool_request'],
      'graphiti-first-guard.py': ['WebSearch|WebFetch', 'mcp__mcp-funnel__bridge_tool_request']
    },
    postToolUseMatchers: {
      'graphiti-retry-guard.py': ['Bash', 'mcp__.*']
    },
    rule: 'graphiti.md',
    commands: ['graphiti/check.md', 'graphiti/end-project.md'],
    localLib: ['secret_patterns.py']
  },

  // === General Rules (no MCP dependency) ===
  stanflux: {
    category: 'general',
    name: 'STANFLUX',
    description: 'Behavior rules for Claude (research, validation, errors)',
    rule: 'stanflux.md'
  },
  pith: {
    category: 'general',
    name: 'PITH',
    description: 'Compact notation format reference',
    rule: 'pith.md'
  },
  '1password': {
    category: 'general',
    name: '1Password',
    description: 'SSH keys & secrets via 1Password Agent',
    rule: '1password.md'
  },

  // === MCP Server Rules ===
  firecrawl: {
    category: 'mcp',
    name: 'Firecrawl',
    description: 'Web search & scraping (firecrawl.dev)',
    hook: {
      type: 'pre-tool-use',
      file: 'firecrawl-guard.py',
      matchers: ['mcp__firecrawl.*', 'mcp__mcp-funnel__bridge_tool_request', 'WebSearch|WebFetch']
    },
    rule: 'mcp-configurations/firecrawl.md'
  },
  context7: {
    category: 'mcp',
    name: 'Context7',
    description: 'GitHub libraries & frameworks research (context7.com)',
    hook: {
      type: 'pre-tool-use',
      file: 'context7-guard.py',
      matchers: ['mcp__context7.*', 'mcp__mcp-funnel__bridge_tool_request']
    },
    rule: 'mcp-configurations/context7.md'
  },
  playwright: {
    category: 'browser-automation',
    name: 'Playwright MCP',
    description: 'Browser automation via MCP Server',
    hook: {
      type: 'pre-tool-use',
      file: 'playwright-guard.py',
      matchers: ['mcp__playwright.*', 'mcp__mcp-funnel__bridge_tool_request', 'Bash']
    },
    rule: 'mcp-configurations/playwright.md'
  },
  'agent-browser': {
    category: 'browser-automation',
    name: 'agent-browser',
    description: 'Browser automation via CLI (vercel-labs/agent-browser) (Recommended)',
    hook: {
      type: 'pre-tool-use',
      file: 'agent-browser-guard.py',
      matchers: ['Bash', 'mcp__mcp-funnel__bridge_tool_request']
    },
    rule: 'mcp-configurations/agent-browser.md'
  },
  github: {
    category: 'mcp',
    name: 'GitHub MCP',
    description: 'GitHub API (Issues, PRs, Repos)',
    rule: 'mcp-configurations/github.md'
  },
  bible: {
    category: 'mcp',
    name: 'Bible',
    description: 'Bible passages via BibleGateway (13 translations)',
    rule: 'mcp-configurations/bible.md'
  },
  businessmap: {
    category: 'mcp',
    name: 'BusinessMap',
    description: 'Portfolio & strategy execution platform',
    rule: 'mcp-configurations/businessmap.md'
  },
  'macos-automator': {
    category: 'mcp',
    name: 'macOS Automator',
    description: 'macOS shortcuts & automation',
    rule: 'mcp-configurations/macos-automator.md'
  },
  morgen: {
    category: 'mcp',
    name: 'Morgen',
    description: 'Calendar & scheduling',
    rule: 'mcp-configurations/morgen.md'
  },
  unifi: {
    category: 'mcp',
    name: 'UniFi',
    description: 'UniFi network management',
    rule: 'mcp-configurations/unifi.md'
  },
  vscode: {
    category: 'mcp',
    name: 'VS Code',
    description: 'VS Code integration',
    rule: 'mcp-configurations/vscode.md'
  },
  whoop: {
    category: 'mcp',
    name: 'Whoop',
    description: 'Fitness & recovery tracking',
    rule: 'mcp-configurations/whoop.md'
  },
  xert: {
    category: 'mcp',
    name: 'Xert',
    description: 'Cycling training analytics',
    rule: 'mcp-configurations/xert.md'
  },

  // === Git Workflow Rules (exclusive - only one can be selected) ===
  'git-workflow-github-flow': {
    category: 'git-workflow',
    name: 'GitHub Flow',
    description: 'Simple branching: main + feature branches (Recommended)',
    hook: {
      type: 'pre-tool-use',
      file: 'git-workflow-guard.py',
      matchers: ['Bash']
    },
    rule: 'git-workflow-github-flow.md'
  },
  'git-workflow-trunk-based': {
    category: 'git-workflow',
    name: 'Trunk-based',
    description: 'Large teams: very short branches + feature flags',
    hook: {
      type: 'pre-tool-use',
      file: 'git-workflow-guard.py',
      matchers: ['Bash']
    },
    rule: 'git-workflow-trunk-based.md'
  },
  'git-workflow-git-flow': {
    category: 'git-workflow',
    name: 'Git Flow',
    description: 'Scheduled releases: main + develop + feature + release + hotfix',
    hook: {
      type: 'pre-tool-use',
      file: 'git-workflow-guard.py',
      matchers: ['Bash']
    },
    rule: 'git-workflow-git-flow.md'
  }
};

// Shared library (always installed if any hook is selected)
const SHARED_LIB = ['session_state.py'];

// Core hooks - always installed when ANY service with hooks is selected
const CORE_HOOKS = {
  'session-start': ['reset-session-flags.py'],
  'pre-tool-use': ['file-context-tracker.py']
};

// Matchers for core PreToolUse hooks
const CORE_HOOK_MATCHERS = {
  'file-context-tracker.py': ['Read|Edit|Write|Glob|Grep']
};

// Stan commands (always installed)
const STAN_COMMANDS = ['stanflux/challenge.md', 'stanflux/help.md', 'stanflux/retro.md'];

// Mandatory rules (always installed - PITH is required to understand hook symbols)
const MANDATORY_RULES = ['pith.md'];

/**
 * Scan entire hierarchy for hook installations
 */
function scanHierarchyForHooks() {
  const home = os.homedir();
  let current = CWD;
  const installations = [];
  const checkedPaths = new Set();

  while (current) {
    const parent = path.dirname(current);
    if (parent === current) break;
    current = parent;
    checkedPaths.add(current);

    const settingsPath = path.join(current, '.claude', 'settings.json');
    if (!fs.existsSync(settingsPath)) continue;

    try {
      const settings = JSON.parse(fs.readFileSync(settingsPath, 'utf8'));
      const hooks = settings.hooks || {};
      const foundHooks = [];

      for (const [hookType, entries] of Object.entries(hooks)) {
        if (!Array.isArray(entries)) continue;
        for (const entry of entries) {
          if (!entry.hooks) continue;
          for (const hook of entry.hooks) {
            if (hook.command && hook.command.includes(PACKAGE_NAME)) {
              foundHooks.push(path.basename(hook.command));
            }
          }
        }
      }

      if (foundHooks.length > 0) {
        const servicesFromHooks = [];
        for (const hookFile of foundHooks) {
          for (const [serviceId, service] of Object.entries(SERVICES)) {
            if (service.hook && service.hook.file === hookFile) {
              servicesFromHooks.push(serviceId);
              break;
            }
            // Check graphiti's multiple hooks
            if (service.hooks) {
              for (const files of Object.values(service.hooks)) {
                if (files.includes(hookFile)) {
                  servicesFromHooks.push(serviceId);
                  break;
                }
              }
            }
          }
        }
        installations.push({
          location: current,
          hooks: [...new Set(foundHooks)],
          services: [...new Set(servicesFromHooks)]
        });
      }
    } catch (e) {
      // Ignore parse errors
    }
  }

  // Check HOME if not already in path
  if (!checkedPaths.has(home)) {
    const settingsPath = path.join(home, '.claude', 'settings.json');
    if (fs.existsSync(settingsPath)) {
      try {
        const settings = JSON.parse(fs.readFileSync(settingsPath, 'utf8'));
        const hooks = settings.hooks || {};
        const foundHooks = [];

        for (const [hookType, entries] of Object.entries(hooks)) {
          if (!Array.isArray(entries)) continue;
          for (const entry of entries) {
            if (!entry.hooks) continue;
            for (const hook of entry.hooks) {
              if (hook.command && hook.command.includes(PACKAGE_NAME)) {
                foundHooks.push(path.basename(hook.command));
              }
            }
          }
        }

        if (foundHooks.length > 0) {
          const servicesFromHooks = [];
          for (const hookFile of foundHooks) {
            for (const [serviceId, service] of Object.entries(SERVICES)) {
              if (service.hook && service.hook.file === hookFile) {
                servicesFromHooks.push(serviceId);
                break;
              }
            }
          }
          installations.push({
            location: home,
            hooks: [...new Set(foundHooks)],
            services: [...new Set(servicesFromHooks)]
          });
        }
      } catch (e) {
        // Ignore
      }
    }
  }

  return installations;
}

/**
 * Check for existing hook installations in parent directories
 */
function checkHierarchyForHooks() {
  const installations = scanHierarchyForHooks();

  if (installations.length === 0) {
    return { found: false, location: null, hooks: [], services: [], duplicates: [] };
  }

  const hookLocations = {};
  for (const inst of installations) {
    for (const hook of inst.hooks) {
      if (!hookLocations[hook]) hookLocations[hook] = [];
      hookLocations[hook].push(inst.location);
    }
  }

  const duplicates = Object.entries(hookLocations)
    .filter(([hook, locations]) => locations.length > 1)
    .map(([hook, locations]) => ({ hook, locations }));

  const closest = installations[0];
  return {
    found: true,
    location: closest.location,
    hooks: closest.hooks,
    services: closest.services,
    duplicates,
    allInstallations: installations
  };
}

/**
 * Validate environment before running commands
 */
function validateEnvironment() {
  if (!CWD) {
    return {
      valid: false,
      error: 'Current working directory does not exist or was deleted.\nPlease cd to a valid directory and try again.'
    };
  }

  try {
    fs.accessSync(CWD, fs.constants.R_OK);
  } catch (e) {
    return {
      valid: false,
      error: `Cannot access current directory: ${CWD}\nCheck permissions and try again.`
    };
  }

  if (fs.existsSync(CLAUDE_DIR)) {
    const stat = fs.statSync(CLAUDE_DIR);
    if (!stat.isDirectory()) {
      return {
        valid: false,
        error: `${CLAUDE_DIR} exists but is not a directory.\nPlease remove or rename it and try again.`
      };
    }
  }

  const testDir = fs.existsSync(CLAUDE_DIR) ? CLAUDE_DIR : CWD;
  try {
    fs.accessSync(testDir, fs.constants.W_OK);
  } catch (e) {
    return {
      valid: false,
      error: `No write permission in: ${testDir}\nCheck permissions and try again.`
    };
  }

  if (!fs.existsSync(SOURCE_HOOKS_DIR) || !fs.existsSync(SOURCE_RULES_DIR)) {
    return {
      valid: false,
      error: 'Package installation is incomplete.\nTry reinstalling: npm install taming-stan'
    };
  }

  return { valid: true };
}

function fileExists(filePath) {
  try {
    fs.lstatSync(filePath);
    return true;
  } catch (e) {
    return false;
  }
}

/**
 * Detect installed services by checking for rule files
 */
function detectInstalledServices() {
  const installed = [];

  for (const [serviceId, service] of Object.entries(SERVICES)) {
    if (!service.rule) continue;
    const rulePath = path.join(RULES_DIR, service.rule);
    if (fileExists(rulePath)) {
      installed.push(serviceId);
    }
  }

  return installed;
}

function removeDirectoryRecursive(dirPath) {
  if (!fs.existsSync(dirPath)) return 0;
  let removed = 0;

  for (const entry of fs.readdirSync(dirPath)) {
    const entryPath = path.join(dirPath, entry);
    if (fs.statSync(entryPath).isDirectory()) {
      removed += removeDirectoryRecursive(entryPath);
    } else {
      fs.unlinkSync(entryPath);
      removed++;
    }
  }
  fs.rmdirSync(dirPath);
  return removed;
}

function log(msg) {
  console.log(`[${PACKAGE_NAME}] ${msg}`);
}

function error(msg) {
  console.error(`[${PACKAGE_NAME}] ERROR: ${msg}`);
}

function ensureDir(dir) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

function copyFile(source, dest) {
  try {
    if (fs.existsSync(dest) || fs.lstatSync(dest).isSymbolicLink()) {
      fs.unlinkSync(dest);
    }
  } catch (e) {
    // File doesn't exist
  }

  try {
    fs.copyFileSync(source, dest);
    if (dest.endsWith('.py')) {
      fs.chmodSync(dest, 0o755);
    }
    return true;
  } catch (e) {
    error(`Failed to copy ${source} to ${dest}: ${e.message}`);
    return false;
  }
}

function deleteFile(filePath) {
  try {
    if (fs.existsSync(filePath)) {
      fs.unlinkSync(filePath);
      return true;
    }
  } catch (e) {
    error(`Failed to delete ${filePath}: ${e.message}`);
  }
  return false;
}

function readState() {
  try {
    if (fs.existsSync(STATE_PATH)) {
      return JSON.parse(fs.readFileSync(STATE_PATH, 'utf8'));
    }
  } catch (e) {
    error(`Failed to read state: ${e.message}`);
  }
  return { installed_services: [], hook_commands: [] };
}

function writeState(state) {
  try {
    ensureDir(CLAUDE_DIR);
    state.installed_at = new Date().toISOString();
    fs.writeFileSync(STATE_PATH, JSON.stringify(state, null, 2));
    return true;
  } catch (e) {
    error(`Failed to write state: ${e.message}`);
    return false;
  }
}

function deleteState() {
  return deleteFile(STATE_PATH);
}

function readRegistry() {
  try {
    if (fs.existsSync(REGISTRY_PATH)) {
      return JSON.parse(fs.readFileSync(REGISTRY_PATH, 'utf8'));
    }
  } catch (e) {
    error(`Failed to read registry: ${e.message}`);
  }
  return { projects: [] };
}

function writeRegistry(registry) {
  try {
    ensureDir(path.dirname(REGISTRY_PATH));
    fs.writeFileSync(REGISTRY_PATH, JSON.stringify(registry, null, 2));
    return true;
  } catch (e) {
    error(`Failed to write registry: ${e.message}`);
    return false;
  }
}

function registerProject(projectPath) {
  if (projectPath === HOME_DIR) return;

  const registry = readRegistry();
  if (!registry.projects.includes(projectPath)) {
    registry.projects.push(projectPath);
    writeRegistry(registry);
  }
}

function unregisterProject(projectPath) {
  const registry = readRegistry();
  const index = registry.projects.indexOf(projectPath);
  if (index > -1) {
    registry.projects.splice(index, 1);
    writeRegistry(registry);
  }
}

function readSettings() {
  try {
    if (fs.existsSync(SETTINGS_PATH)) {
      return JSON.parse(fs.readFileSync(SETTINGS_PATH, 'utf8'));
    }
  } catch (e) {
    error(`Failed to read settings: ${e.message}`);
  }
  return {};
}

function writeSettings(settings) {
  try {
    ensureDir(CLAUDE_DIR);
    fs.writeFileSync(SETTINGS_PATH, JSON.stringify(settings, null, 2));
    return true;
  } catch (e) {
    error(`Failed to write settings: ${e.message}`);
    return false;
  }
}

function getServicesByCategory(category) {
  return Object.entries(SERVICES)
    .filter(([_, service]) => service.category === category)
    .map(([id, service]) => ({ id, ...service }));
}

async function promptCategorySelection(category, title, subtitle, currentlySelected, lockedServices = [], parentLocation = null) {
  const services = getServicesByCategory(category);
  const previouslySelected = new Set(currentlySelected.filter(id => SERVICES[id]?.category === category));
  const lockedSet = new Set(lockedServices.filter(id => SERVICES[id]?.category === category));

  const choices = services.map(service => {
    const isLocked = lockedSet.has(service.id);
    const hasHook = service.hook || service.hooks;
    const suffix = hasHook ? ' (Rule + Hook)' : ' (Rule only)';
    const lockedSuffix = isLocked ? ` [from ${parentLocation}]` : '';

    return {
      name: `${service.name} - ${service.description}${suffix}${lockedSuffix}`,
      value: service.id,
      checked: previouslySelected.has(service.id) || isLocked,
      disabled: isLocked ? 'inherited' : false
    };
  });

  console.log('');
  console.log(`=== ${title} ===`);
  console.log(subtitle);

  const { selected } = await inquirer.prompt([{
    type: 'checkbox',
    name: 'selected',
    message: 'Use arrow keys to navigate, Space to toggle, Enter to confirm:',
    choices,
    pageSize: 15
  }]);

  const lockedInCategory = [...lockedSet];
  return [...new Set([...selected, ...lockedInCategory])];
}

async function promptExclusiveSelection(category, title, subtitle, currentlySelected, lockedServices = [], parentLocation = null) {
  const services = getServicesByCategory(category);
  const previouslySelected = currentlySelected.find(id => SERVICES[id]?.category === category);
  const lockedInCategory = lockedServices.find(id => SERVICES[id]?.category === category);

  if (lockedInCategory) {
    const lockedService = SERVICES[lockedInCategory];
    console.log('');
    console.log(`=== ${title} ===`);
    console.log(subtitle);
    console.log(`  [check] ${lockedService.name} [from ${parentLocation}]`);
    return [lockedInCategory];
  }

  const choices = [
    { name: '(none)', value: null },
    ...services.map(service => ({
      name: `${service.name} - ${service.description}`,
      value: service.id
    }))
  ];

  console.log('');
  console.log(`=== ${title} ===`);
  console.log(subtitle);

  const { selected } = await inquirer.prompt([{
    type: 'list',
    name: 'selected',
    message: 'Use arrow keys to navigate, Enter to select (only one):',
    choices,
    default: previouslySelected || null,
    pageSize: 10
  }]);

  return selected ? [selected] : [];
}

async function promptServiceSelection(currentlyInstalled, lockedServices = [], parentLocation = null) {
  console.log('\n=== taming-stan Installation ===');
  console.log(`Target: ${CLAUDE_DIR}`);

  if (lockedServices.length > 0) {
    console.log(`\n[pin] Services with hooks inherited from: ${parentLocation}`);
    console.log('   (shown as disabled, rules will be installed locally)\n');
  }

  // Part 1: Graphiti (Memory)
  const graphitiSelected = await promptCategorySelection(
    'graphiti',
    'Graphiti (Long-term Memory)',
    'Graphiti provides knowledge graph memory across sessions.',
    currentlyInstalled,
    lockedServices,
    parentLocation
  );

  // Part 2: General Rules
  const generalSelected = await promptCategorySelection(
    'general',
    'General Rules',
    'These rules apply to all projects, regardless of MCP servers.',
    currentlyInstalled,
    lockedServices,
    parentLocation
  );

  // Part 3: Git Workflow (exclusive)
  const gitWorkflowSelected = await promptExclusiveSelection(
    'git-workflow',
    'Git Workflow (choose one)',
    'SemVer, Changelog, Conventional Commits + your branching strategy:',
    currentlyInstalled,
    lockedServices,
    parentLocation
  );

  // Part 4: Browser Automation (exclusive)
  const browserSelected = await promptExclusiveSelection(
    'browser-automation',
    'Browser Automation (choose one)',
    'Web testing & automation:',
    currentlyInstalled,
    lockedServices,
    parentLocation
  );

  // Part 5: MCP Server Rules
  const mcpSelected = await promptCategorySelection(
    'mcp',
    'MCP Server Rules',
    'Select which MCP servers you have installed (separately):',
    currentlyInstalled,
    lockedServices,
    parentLocation
  );

  return [...graphitiSelected, ...generalSelected, ...gitWorkflowSelected, ...browserSelected, ...mcpSelected];
}

function installServices(selectedServices, options = {}) {
  const {
    lockedServices = [],
    hierarchyHooks = []
  } = options;

  log('Installing selected services...');

  const hookInHierarchy = (hookFile) => hierarchyHooks.includes(hookFile);

  // Determine which services need LOCAL hooks
  const localHookServices = selectedServices.filter(id => {
    const service = SERVICES[id];
    if (service?.hook && !hookInHierarchy(service.hook.file)) return true;
    if (service?.hooks) {
      for (const files of Object.values(service.hooks)) {
        for (const file of files) {
          if (!hookInHierarchy(file)) return true;
        }
      }
    }
    return false;
  });
  const needsLocalHooks = localHookServices.length > 0;

  // Check core hooks
  const coreHookFiles = Object.values(CORE_HOOKS).flat();
  const allCoreHooksInHierarchy = coreHookFiles.every(f => hierarchyHooks.includes(f));

  // Create directories
  if (needsLocalHooks || !allCoreHooksInHierarchy) {
    ensureDir(path.join(HOOKS_DIR, 'pre-tool-use'));
    ensureDir(path.join(HOOKS_DIR, 'post-tool-use'));
    ensureDir(path.join(HOOKS_DIR, 'session-start'));
    ensureDir(path.join(HOOKS_DIR, 'user-prompt-submit'));
    ensureDir(path.join(HOOKS_DIR, 'lib'));
  }
  ensureDir(path.join(RULES_DIR, 'mcp-configurations'));
  ensureDir(path.join(COMMANDS_DIR, 'graphiti'));
  ensureDir(path.join(COMMANDS_DIR, 'stanflux'));

  let installed = { hooks: 0, rules: 0, commands: 0 };
  const hookCommands = [];

  // Install shared library
  if (needsLocalHooks) {
    for (const libFile of SHARED_LIB) {
      const source = path.join(SOURCE_LIB_DIR, libFile);
      const dest = path.join(HOOKS_DIR, 'lib', libFile);
      if (fs.existsSync(source) && copyFile(source, dest)) {
        log(`Installed lib: ${libFile}`);
      }
    }
  }

  // Install core hooks
  if (needsLocalHooks && !allCoreHooksInHierarchy) {
    for (const [hookType, files] of Object.entries(CORE_HOOKS)) {
      for (const file of files) {
        const source = path.join(SOURCE_HOOKS_DIR, hookType, file);
        const dest = path.join(HOOKS_DIR, hookType, file);
        if (fs.existsSync(source) && copyFile(source, dest)) {
          installed.hooks++;
          hookCommands.push(dest);
          log(`Installed core hook: ${file}`);
        }
      }
    }
  }

  // Install stan commands (always)
  for (const cmd of STAN_COMMANDS) {
    const source = path.join(SOURCE_COMMANDS_DIR, cmd);
    const dest = path.join(COMMANDS_DIR, cmd);
    ensureDir(path.dirname(dest));
    if (fs.existsSync(source) && copyFile(source, dest)) {
      installed.commands++;
    }
  }

  // Install mandatory rules (always - PITH required to understand hook symbols)
  for (const rule of MANDATORY_RULES) {
    const source = path.join(SOURCE_RULES_DIR, rule);
    const dest = path.join(RULES_DIR, rule);
    if (fs.existsSync(source) && copyFile(source, dest)) {
      installed.rules++;
      log(`Installed mandatory rule: ${rule}`);
    }
  }

  // Install selected services
  const allServicesToInstall = [...new Set([...selectedServices, ...lockedServices])];

  for (const serviceId of allServicesToInstall) {
    const service = SERVICES[serviceId];
    if (!service) continue;

    const isLocked = lockedServices.includes(serviceId);

    // Copy single hook (simple services)
    if (service.hook && !hookInHierarchy(service.hook.file)) {
      const hookSource = path.join(SOURCE_HOOKS_DIR, service.hook.type, service.hook.file);
      const hookDest = path.join(HOOKS_DIR, service.hook.type, service.hook.file);
      if (fs.existsSync(hookSource) && copyFile(hookSource, hookDest)) {
        installed.hooks++;
        hookCommands.push(hookDest);
        log(`Installed hook: ${service.hook.file}`);
      }
    }

    // Copy multiple hooks (graphiti)
    if (service.hooks) {
      for (const [hookType, files] of Object.entries(service.hooks)) {
        for (const file of files) {
          if (!hookInHierarchy(file)) {
            const hookSource = path.join(SOURCE_HOOKS_DIR, hookType, file);
            const hookDest = path.join(HOOKS_DIR, hookType, file);
            if (fs.existsSync(hookSource) && copyFile(hookSource, hookDest)) {
              installed.hooks++;
              hookCommands.push(hookDest);
              log(`Installed hook: ${file}`);
            }
          }
        }
      }
    }

    // Copy local library (graphiti)
    if (service.localLib) {
      for (const libFile of service.localLib) {
        const source = path.join(SOURCE_LIB_DIR, libFile);
        const dest = path.join(HOOKS_DIR, 'lib', libFile);
        if (fs.existsSync(source) && copyFile(source, dest)) {
          log(`Installed lib: ${libFile}`);
        }
      }
    }

    // Copy rule
    if (service.rule) {
      const ruleSource = path.join(SOURCE_RULES_DIR, service.rule);
      const ruleDest = path.join(RULES_DIR, service.rule);
      ensureDir(path.dirname(ruleDest));
      if (fs.existsSync(ruleSource) && copyFile(ruleSource, ruleDest)) {
        installed.rules++;
        log(`Installed rule: ${service.rule}${isLocked ? ' (from hierarchy)' : ''}`);
      }
    }

    // Copy commands (graphiti)
    if (service.commands) {
      for (const cmd of service.commands) {
        const source = path.join(SOURCE_COMMANDS_DIR, cmd);
        const dest = path.join(COMMANDS_DIR, cmd);
        ensureDir(path.dirname(dest));
        if (fs.existsSync(source) && copyFile(source, dest)) {
          installed.commands++;
        }
      }
    }
  }

  // Update settings.json
  updateSettings(selectedServices, hookCommands, hierarchyHooks);

  // Write state file
  const allInstalledServices = [...new Set([...selectedServices, ...lockedServices])];
  if (allInstalledServices.length === 0) {
    deleteState();
    log('Removed state file (no services installed)');
  } else {
    writeState({
      installed_services: allInstalledServices,
      hook_commands: hookCommands
    });
  }

  // Register project
  registerProject(CWD);

  log(`\nInstallation complete: ${installed.hooks} hooks, ${installed.rules} rules, ${installed.commands} commands`);
}

function updateSettings(selectedServices, newHookCommands, hierarchyHooks = []) {
  const settings = readSettings();
  if (!settings.hooks) settings.hooks = {};

  // Match our package AND legacy packages that should be cleaned up
  const isOurHook = (command) => command && (
    command.includes(PACKAGE_NAME) ||
    command.includes('shared-claude-rules') ||
    command.includes('claude-hooks-core') ||
    command.includes('graphiti-claude-integration')
  );

  // Clean up all our package's hook entries
  for (const hookType of ['PreToolUse', 'PostToolUse', 'SessionStart', 'UserPromptSubmit']) {
    if (settings.hooks[hookType]) {
      settings.hooks[hookType] = settings.hooks[hookType].map(entry => {
        if (!entry.hooks) return entry;
        entry.hooks = entry.hooks.filter(h => !isOurHook(h.command));
        return entry;
      }).filter(entry => entry.hooks && entry.hooks.length > 0);
    }
  }

  const hasHooks = selectedServices.some(id => SERVICES[id]?.hook || SERVICES[id]?.hooks);

  if (hasHooks && newHookCommands.length > 0) {
    // SessionStart hooks
    if (!settings.hooks.SessionStart) settings.hooks.SessionStart = [];

    // Core session hook
    const resetHookPath = path.join(HOOKS_DIR, 'session-start', 'reset-session-flags.py');
    if (newHookCommands.includes(resetHookPath)) {
      settings.hooks.SessionStart.push({
        hooks: [{ type: 'command', command: resetHookPath }],
        once: true
      });
    }

    // Graphiti context loader
    const graphitiContextPath = path.join(HOOKS_DIR, 'session-start', 'graphiti-context-loader.py');
    if (newHookCommands.includes(graphitiContextPath)) {
      settings.hooks.SessionStart.push({
        hooks: [{ type: 'command', command: graphitiContextPath }],
        once: true
      });
    }

    // UserPromptSubmit hooks
    if (!settings.hooks.UserPromptSubmit) settings.hooks.UserPromptSubmit = [];
    const userPromptHooks = newHookCommands.filter(c => c.includes('/user-prompt-submit/'));
    for (const hookPath of userPromptHooks) {
      settings.hooks.UserPromptSubmit.push({
        hooks: [{ type: 'command', command: hookPath }]
      });
    }

    // Core PreToolUse hooks
    if (!settings.hooks.PreToolUse) settings.hooks.PreToolUse = [];
    for (const [hookFile, matchers] of Object.entries(CORE_HOOK_MATCHERS)) {
      const hookPath = path.join(HOOKS_DIR, 'pre-tool-use', hookFile);
      if (newHookCommands.includes(hookPath)) {
        for (const matcher of matchers) {
          const existing = settings.hooks.PreToolUse.find(e => e.matcher === matcher);
          if (existing) {
            if (!existing.hooks.some(h => h.command === hookPath)) {
              existing.hooks.push({ type: 'command', command: hookPath });
            }
          } else {
            settings.hooks.PreToolUse.push({
              matcher,
              hooks: [{ type: 'command', command: hookPath }]
            });
          }
        }
      }
    }

    // PostToolUse hooks
    if (!settings.hooks.PostToolUse) settings.hooks.PostToolUse = [];
  }

  // Service-specific hooks
  const matcherHooks = {};
  const postToolUseMatcherHooks = {};

  for (const serviceId of selectedServices) {
    const service = SERVICES[serviceId];
    if (!service) continue;

    // Simple hook (most services)
    if (service.hook) {
      const hookPath = path.join(HOOKS_DIR, service.hook.type, service.hook.file);
      const isInHierarchy = hierarchyHooks.includes(service.hook.file);
      if (!isInHierarchy && fs.existsSync(hookPath)) {
        for (const matcher of service.hook.matchers) {
          if (!matcherHooks[matcher]) matcherHooks[matcher] = [];
          if (!matcherHooks[matcher].some(h => h.command === hookPath)) {
            matcherHooks[matcher].push({ type: 'command', command: hookPath });
          }
        }
      }
    }

    // Multiple hooks (graphiti)
    if (service.preToolUseMatchers) {
      for (const [hookFile, matchers] of Object.entries(service.preToolUseMatchers)) {
        const hookPath = path.join(HOOKS_DIR, 'pre-tool-use', hookFile);
        const isInHierarchy = hierarchyHooks.includes(hookFile);
        if (!isInHierarchy && fs.existsSync(hookPath)) {
          for (const matcher of matchers) {
            if (!matcherHooks[matcher]) matcherHooks[matcher] = [];
            if (!matcherHooks[matcher].some(h => h.command === hookPath)) {
              matcherHooks[matcher].push({ type: 'command', command: hookPath });
            }
          }
        }
      }
    }

    if (service.postToolUseMatchers) {
      for (const [hookFile, matchers] of Object.entries(service.postToolUseMatchers)) {
        const hookPath = path.join(HOOKS_DIR, 'post-tool-use', hookFile);
        const isInHierarchy = hierarchyHooks.includes(hookFile);
        if (!isInHierarchy && fs.existsSync(hookPath)) {
          for (const matcher of matchers) {
            if (!postToolUseMatcherHooks[matcher]) postToolUseMatcherHooks[matcher] = [];
            if (!postToolUseMatcherHooks[matcher].some(h => h.command === hookPath)) {
              postToolUseMatcherHooks[matcher].push({ type: 'command', command: hookPath });
            }
          }
        }
      }
    }
  }

  // Add PreToolUse entries
  for (const [matcher, hooks] of Object.entries(matcherHooks)) {
    const existing = settings.hooks.PreToolUse.find(e => e.matcher === matcher);
    if (existing) {
      for (const hook of hooks) {
        if (!existing.hooks.some(h => h.command === hook.command)) {
          existing.hooks.push(hook);
        }
      }
    } else {
      settings.hooks.PreToolUse.push({ matcher, hooks });
    }
  }

  // Add PostToolUse entries
  for (const [matcher, hooks] of Object.entries(postToolUseMatcherHooks)) {
    const existing = settings.hooks.PostToolUse.find(e => e.matcher === matcher);
    if (existing) {
      for (const hook of hooks) {
        if (!existing.hooks.some(h => h.command === hook.command)) {
          existing.hooks.push(hook);
        }
      }
    } else {
      settings.hooks.PostToolUse.push({ matcher, hooks });
    }
  }

  // Clean up empty entries
  for (const hookType of Object.keys(settings.hooks)) {
    settings.hooks[hookType] = settings.hooks[hookType].filter(
      entry => entry.hooks && entry.hooks.length > 0
    );
    if (settings.hooks[hookType].length === 0) {
      delete settings.hooks[hookType];
    }
  }

  writeSettings(settings);
  log('Updated settings.json');
}

function cleanupEmptyDirectories(baseDir = CWD) {
  const claudeDir = path.join(baseDir, '.claude');
  const hooksDir = path.join(claudeDir, 'hooks', PACKAGE_NAME);
  const rulesDir = path.join(claudeDir, 'rules', PACKAGE_NAME);
  const commandsDir = path.join(claudeDir, 'commands', PACKAGE_NAME);

  function removeEmptyDirsRecursive(dir) {
    if (!fs.existsSync(dir)) return;

    try {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        if (entry.isDirectory() && entry.name !== '__pycache__') {
          removeEmptyDirsRecursive(path.join(dir, entry.name));
        }
      }

      const remaining = fs.readdirSync(dir);
      const nonCacheRemaining = remaining.filter(f => f !== '__pycache__');

      if (nonCacheRemaining.length === 0) {
        const pycacheDir = path.join(dir, '__pycache__');
        if (fs.existsSync(pycacheDir)) {
          removeDirectoryRecursive(pycacheDir);
        }
        fs.rmdirSync(dir);
      }
    } catch (e) { /* ignore */ }
  }

  for (const dir of [hooksDir, rulesDir, commandsDir]) {
    removeEmptyDirsRecursive(dir);
  }
}

async function uninstall() {
  log('Uninstalling all services...');

  const installed = detectInstalledServices();
  let removed = { hooks: 0, rules: 0, commands: 0 };

  // Remove all service hooks and rules
  for (const serviceId of installed) {
    const service = SERVICES[serviceId];
    if (!service) continue;

    // Remove single hook
    if (service.hook) {
      const hookPath = path.join(HOOKS_DIR, service.hook.type, service.hook.file);
      if (deleteFile(hookPath)) {
        removed.hooks++;
        log(`Removed: ${service.hook.file}`);
      }
    }

    // Remove multiple hooks (graphiti)
    if (service.hooks) {
      for (const [hookType, files] of Object.entries(service.hooks)) {
        for (const file of files) {
          const hookPath = path.join(HOOKS_DIR, hookType, file);
          if (deleteFile(hookPath)) {
            removed.hooks++;
            log(`Removed: ${file}`);
          }
        }
      }
    }

    // Remove local lib (graphiti)
    if (service.localLib) {
      for (const libFile of service.localLib) {
        const libPath = path.join(HOOKS_DIR, 'lib', libFile);
        deleteFile(libPath);
      }
    }

    // Remove rule
    if (service.rule) {
      const rulePath = path.join(RULES_DIR, service.rule);
      if (deleteFile(rulePath)) {
        removed.rules++;
        log(`Removed: ${service.rule}`);
      }
    }

    // Remove commands
    if (service.commands) {
      for (const cmd of service.commands) {
        const cmdPath = path.join(COMMANDS_DIR, cmd);
        if (deleteFile(cmdPath)) {
          removed.commands++;
        }
      }
    }
  }

  // Remove core hooks
  for (const [hookType, files] of Object.entries(CORE_HOOKS)) {
    for (const file of files) {
      const hookPath = path.join(HOOKS_DIR, hookType, file);
      if (deleteFile(hookPath)) {
        removed.hooks++;
        log(`Removed core hook: ${file}`);
      }
    }
  }

  // Remove shared library
  for (const libFile of SHARED_LIB) {
    const libPath = path.join(HOOKS_DIR, 'lib', libFile);
    if (deleteFile(libPath)) {
      log(`Removed lib: ${libFile}`);
    }
  }

  // Remove stan commands
  for (const cmd of STAN_COMMANDS) {
    const cmdPath = path.join(COMMANDS_DIR, cmd);
    deleteFile(cmdPath);
  }

  // Remove mandatory rules
  for (const rule of MANDATORY_RULES) {
    const rulePath = path.join(RULES_DIR, rule);
    deleteFile(rulePath);
  }

  // Clean settings.json (including legacy packages)
  const settings = readSettings();
  if (settings.hooks) {
    const isLegacyOrOurs = (cmd) => cmd && (
      cmd.includes(PACKAGE_NAME) ||
      cmd.includes('shared-claude-rules') ||
      cmd.includes('claude-hooks-core') ||
      cmd.includes('graphiti-claude-integration')
    );
    for (const hookType of Object.keys(settings.hooks)) {
      settings.hooks[hookType] = settings.hooks[hookType].map(entry => {
        if (!entry.hooks) return entry;
        entry.hooks = entry.hooks.filter(h => !h.command || !isLegacyOrOurs(h.command));
        return entry;
      }).filter(entry => entry.hooks && entry.hooks.length > 0);
      if (settings.hooks[hookType].length === 0) {
        delete settings.hooks[hookType];
      }
    }
    writeSettings(settings);
    log('Updated settings.json');
  }

  // Clean up legacy hook/rule folders
  const legacyFolders = [
    path.join(CLAUDE_DIR, 'hooks', 'shared-claude-rules'),
    path.join(CLAUDE_DIR, 'hooks', 'claude-hooks-core'),
    path.join(CLAUDE_DIR, 'hooks', 'graphiti-claude-integration'),
    path.join(CLAUDE_DIR, 'rules', 'shared-claude-rules'),
    path.join(CLAUDE_DIR, 'rules', 'claude-hooks-core'),
    path.join(CLAUDE_DIR, 'rules', 'graphiti-claude-integration')
  ];
  for (const folder of legacyFolders) {
    if (fs.existsSync(folder)) {
      try {
        fs.rmSync(folder, { recursive: true });
        log(`Removed legacy folder: ${path.basename(folder)}`);
      } catch (e) {
        // Ignore errors
      }
    }
  }

  // Clean up
  cleanupEmptyDirectories();
  if (deleteState()) {
    log('Removed state file');
  }
  unregisterProject(CWD);

  log(`\nUninstall complete: removed ${removed.hooks} hooks, ${removed.rules} rules, ${removed.commands} commands`);
}

function status() {
  console.log('\n=== taming-stan Status ===');
  console.log(`Target: ${CLAUDE_DIR}\n`);

  const installed = detectInstalledServices();

  // Graphiti
  console.log('Graphiti (Memory):');
  for (const service of getServicesByCategory('graphiti')) {
    const isInstalled = installed.includes(service.id);
    console.log(`  ${service.name}: ${isInstalled ? '  Installed' : '  Not installed'}`);
  }

  // General Rules
  console.log('\nGeneral Rules:');
  for (const service of getServicesByCategory('general')) {
    const isInstalled = installed.includes(service.id);
    console.log(`  ${service.name}: ${isInstalled ? '  Installed' : '  Not installed'}`);
  }

  // Git Workflow
  console.log('\nGit Workflow (one of):');
  for (const service of getServicesByCategory('git-workflow')) {
    const isInstalled = installed.includes(service.id);
    console.log(`  ${service.name}: ${isInstalled ? '[check] Active' : '  Not selected'}`);
  }

  // Browser Automation
  console.log('\nBrowser Automation (one of):');
  for (const service of getServicesByCategory('browser-automation')) {
    const isInstalled = installed.includes(service.id);
    console.log(`  ${service.name}: ${isInstalled ? '[check] Active' : '  Not selected'}`);
  }

  // MCP Server Rules
  console.log('\nMCP Server Rules:');
  for (const service of getServicesByCategory('mcp')) {
    const isInstalled = installed.includes(service.id);
    const hookInfo = service.hook ? ' (with hook)' : '';
    console.log(`  ${service.name}${hookInfo}: ${isInstalled ? '  Installed' : '  Not installed'}`);
  }

  // Core hooks
  console.log('\nCore Hooks (session management):');
  for (const [hookType, files] of Object.entries(CORE_HOOKS)) {
    for (const file of files) {
      const hookPath = path.join(HOOKS_DIR, hookType, file);
      const exists = fs.existsSync(hookPath);
      console.log(`  ${file}: ${exists ? '  Installed' : '  Not installed'}`);
    }
  }

  // Shared library
  const libInstalled = SHARED_LIB.every(f => fs.existsSync(path.join(HOOKS_DIR, 'lib', f)));
  console.log(`\nShared library: ${libInstalled ? '  Installed' : '  Not installed'}`);

  // State file
  const stateExists = fs.existsSync(STATE_PATH);
  console.log(`State file: ${stateExists ? '  Exists' : '  Not found'}`);

  console.log('');
}

function parseInstallArgs(args) {
  if (args.length === 0) {
    return { interactive: true, services: [] };
  }

  if (args.includes('--all')) {
    const allServices = Object.keys(SERVICES).filter(id => {
      const service = SERVICES[id];
      if (service.category === 'git-workflow') return id === 'git-workflow-github-flow';
      if (service.category === 'browser-automation') return id === 'agent-browser';
      return true;
    });
    return { interactive: false, services: allServices };
  }

  const services = [];
  for (const arg of args) {
    if (arg.startsWith('--')) continue;
    const parts = arg.split(',').map(s => s.trim()).filter(Boolean);
    services.push(...parts);
  }

  const validServices = Object.keys(SERVICES);
  const invalid = services.filter(s => !validServices.includes(s));
  if (invalid.length > 0) {
    error(`Unknown services: ${invalid.join(', ')}`);
    console.log(`\nValid services: ${validServices.join(', ')}`);
    process.exit(1);
  }

  return { interactive: services.length === 0, services };
}

async function main() {
  const command = process.argv[2];
  const args = process.argv.slice(3);

  const needsValidation = ['install', 'uninstall', 'status'];

  if (needsValidation.includes(command)) {
    const validation = validateEnvironment();
    if (!validation.valid) {
      error(validation.error);
      process.exit(1);
    }
  }

  switch (command) {
    case 'install':
      const { interactive, services } = parseInstallArgs(args);
      let selected;

      const hierarchyCheck = checkHierarchyForHooks();

      if (hierarchyCheck.duplicates && hierarchyCheck.duplicates.length > 0) {
        console.log('\n[warning] DUPLICATE HOOKS DETECTED!');
        console.log('   The following hooks are installed in multiple locations:\n');
        for (const dup of hierarchyCheck.duplicates) {
          console.log(`   ${dup.hook}:`);
          for (const loc of dup.locations) {
            console.log(`     - ${loc}`);
          }
        }
        console.log('\n   This causes hooks to run MULTIPLE times!');
        console.log('   Run installer in each location to clean up.\n');
      }

      if (hierarchyCheck.allInstallations && hierarchyCheck.allInstallations.length > 0) {
        console.log('\n[pin] Hooks found in HOME + hierarchy:');
        for (const inst of hierarchyCheck.allInstallations) {
          console.log(`   ${inst.location}: ${inst.hooks.join(', ')}`);
        }
        console.log('   (will be updated after selection)\n');
      }

      if (interactive) {
        if (!process.stdin.isTTY) {
          error('Interactive mode requires a TTY terminal.\n\nUse one of these instead:\n  npx taming-stan install --all\n  npx taming-stan install graphiti,firecrawl,stanflux\n\nOr run from an interactive terminal.');
          process.exit(1);
        }

        const alreadyInstalled = detectInstalledServices();

        if (hierarchyCheck.found) {
          // If installing in the SAME location as hierarchy, update hooks instead of skipping
          const isInstallingInHierarchyLocation = CWD === hierarchyCheck.location;
          selected = await promptServiceSelection(
            alreadyInstalled,
            isInstallingInHierarchyLocation ? [] : hierarchyCheck.services,
            isInstallingInHierarchyLocation ? null : hierarchyCheck.location
          );
          if (isInstallingInHierarchyLocation) {
            installServices(selected);  // No hierarchyHooks = will overwrite existing
          } else {
            installServices(selected, {
              lockedServices: hierarchyCheck.services,
              hierarchyHooks: hierarchyCheck.hooks
            });
          }
        } else {
          selected = await promptServiceSelection(alreadyInstalled);
          installServices(selected);
        }
      } else {
        selected = services;
        log(`Non-interactive mode: installing ${selected.length} services`);

        if (hierarchyCheck.found) {
          // If installing in the SAME location as hierarchy, update hooks instead of skipping
          const isInstallingInHierarchyLocation = CWD === hierarchyCheck.location;
          if (isInstallingInHierarchyLocation) {
            log(`Updating hooks in: ${hierarchyCheck.location}`);
            installServices(selected);  // No hierarchyHooks = will overwrite existing
          } else {
            log(`Hooks inherited from: ${hierarchyCheck.location}`);
            installServices(selected, {
              lockedServices: hierarchyCheck.services,
              hierarchyHooks: hierarchyCheck.hooks
            });
          }
        } else {
          installServices(selected);
        }
      }

      if (hierarchyCheck.found) {
        const home = os.homedir();
        console.log(`\n[bulb] To uninstall hooks from ${hierarchyCheck.location === home ? 'HOME' : 'hierarchy'}:`);
        console.log(`   cd ${hierarchyCheck.location} && npx taming-stan uninstall`);
      }
      break;

    case 'uninstall':
      await uninstall();
      break;

    case 'status':
      status();
      break;

    default:
      console.log(`
taming-stan - All-in-one Claude Code enhancement

Usage:
  npx taming-stan install                     - Interactive mode
  npx taming-stan install <services...>      - Install specific services
  npx taming-stan install --all              - Install all services
  npx taming-stan uninstall                  - Remove all installed services
  npx taming-stan status                     - Show installation status

Services: ${Object.keys(SERVICES).join(', ')}

Examples:
  npx taming-stan install graphiti firecrawl stanflux
  npx taming-stan install graphiti,firecrawl,stanflux
  npx taming-stan install --all

Installation target is relative to current directory:
  cd ~        -> installs to ~/.claude/
  cd /project -> installs to /project/.claude/
`);
  }
}

main().catch(err => {
  error(err.message);
  process.exit(1);
});
