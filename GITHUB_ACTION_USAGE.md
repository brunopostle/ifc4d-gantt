# GitHub Action for IFC Gantt Charts

This repository includes a GitHub Action that automatically generates interactive Gantt charts from IFC files and publishes them via GitHub Pages.

## Features

- **Automatic Generation**: Runs whenever IFC files are pushed to the repository
- **Multi-Version Support**: Separate charts for each commit and tag
- **GitHub Pages Deployment**: View charts directly in your browser via GitHub Pages
- **Index Pages**: Automatically generated navigation to find charts by commit or tag

## Setup Instructions

### 1. Enable GitHub Pages

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Pages**
3. Under **Source**, select **GitHub Actions**

### 2. Add the Workflow File

Copy the example workflow file to your IFC repository:

```bash
# In your IFC repository (not the ifc4d-gantt repository)
mkdir -p .github/workflows
curl -o .github/workflows/generate-gantt-charts.yml \
  https://raw.githubusercontent.com/brunopostle/ifc4d-gantt/main/workflows/generate-gantt-charts.yml
```

Or manually copy `workflows/generate-gantt-charts.yml` from the ifc4d-gantt repository to `.github/workflows/generate-gantt-charts.yml` in your IFC repository.

### 3. Commit and Push

```bash
git add .github/workflows/ifc4d-gantt-charts.yml
git commit -m "Add IFC Gantt chart generation workflow"
git push
```

The workflow will run automatically on the next push of an IFC file.

## How It Works

### Triggers

The workflow runs when:
- IFC files (`.ifc`) are pushed to `main` or `master` branch
- A release is created or published
- Manually triggered via the Actions tab

### Output Structure

The generated GitHub Pages site has this structure:

```
https://username.github.io/repo-name/
├── index.html                          # Root index with links to all versions
├── commits/
│   ├── abc1234/
│   │   ├── index.html                 # List of charts for this commit
│   │   ├── model1.html                # Generated Gantt chart
│   │   └── subfolder_model2.html      # Generated Gantt chart
│   └── def5678/
│       └── ...
└── tags/
    ├── v1.0.0/
    │   ├── index.html                 # List of charts for this tag
    │   └── *.html                     # Generated Gantt charts
    └── v2.0.0/
        └── ...
```

### Viewing Charts

1. **Root Index**: `https://username.github.io/repo-name/`
   - Shows links to the latest version and all historical versions

2. **Latest Commit**: `https://username.github.io/repo-name/commits/abc1234/`
   - View charts from a specific commit

3. **Tagged Release**: `https://username.github.io/repo-name/tags/v1.0.0/`
   - View charts from a specific release version

## Customization

### Modify Branch Triggers

Edit `.github/workflows/ifc4d-gantt-charts.yml`:

```yaml
on:
  push:
    branches:
      - main
      - develop  # Add additional branches
    paths:
      - '**.ifc'
```

### Change File Pattern

To process files other than `*.ifc`:

```yaml
paths:
  - '**.ifc'
  - '**.ifcxml'  # Add additional patterns
```

And update the find command in the workflow:

```bash
find . -name "*.ifc" -o -name "*.ifcxml" -type f | while read -r ifc_file; do
```

### Add Custom Styling

The generated index pages can be customized by editing the HTML/CSS in the workflow file under the "Generate root index.html" section.

## Workflow Permissions

The workflow requires these permissions (already configured):
- `contents: read` - To checkout the repository
- `pages: write` - To deploy to GitHub Pages
- `id-token: write` - For GitHub Pages deployment authentication

## Troubleshooting

### Charts Not Appearing

1. Check the **Actions** tab to see if the workflow ran successfully
2. Verify GitHub Pages is enabled in repository settings
3. Check that IFC files were actually modified in the commit

### Manual Trigger

You can manually trigger the workflow:
1. Go to the **Actions** tab
2. Select **Generate IFC Gantt Charts**
3. Click **Run workflow**

### Viewing Logs

To debug issues:
1. Go to **Actions** tab
2. Click on the failed workflow run
3. Expand the step logs to see detailed output

## Example Repository

For a working example, see: [link to example repo with IFC files]

## Requirements

- GitHub repository with IFC files
- GitHub Pages enabled
- Public repository (or GitHub Pro/Enterprise for private repos with Pages)

## Notes

- Charts are regenerated on each push, but old versions are preserved in separate directories
- The `_site` directory is never committed to the repository; it only exists during workflow execution
