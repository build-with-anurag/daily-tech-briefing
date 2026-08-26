function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    var folder = DriveApp.getFolderById("1XOso76g1UDFn_cocI04wpIcsslmKIff3");
    
    // Create new Google Doc
    var doc = DocumentApp.create(data.title);
    var body = doc.getBody();
    body.clear();
    
    // Set clean margins (0.75 inch)
    body.setMarginTop(54);
    body.setMarginBottom(54);
    body.setMarginLeft(54);
    body.setMarginRight(54);
    
    // Parse and apply high-end typography & styles
    buildStyledDocument(body, data.content);
    
    doc.saveAndClose();
    
    // Move to the target folder
    var file = DriveApp.getFileById(doc.getId());
    folder.addFile(file);
    DriveApp.getRootFolder().removeFile(file);
    
    return ContentService.createTextOutput(JSON.stringify({
      status: "success",
      title: data.title,
      url: doc.getUrl()
    })).setMimeType(ContentService.MimeType.JSON);
    
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({
      status: "error",
      message: err.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

function buildStyledDocument(body, text) {
  var lines = text.split(/\r?\n/);
  
  // Color Palette
  var COLOR_PRIMARY = "#0F172A";    // Deep Navy
  var COLOR_TEXT = "#1E293B";       // Dark Slate Text
  var COLOR_MUTED = "#475569";      // Muted Slate
  var COLOR_LINK = "#1A56DB";       // Blue
  var FONT_FAMILY = "Arial";
  
  for (var i = 0; i < lines.length; i++) {
    var line = lines[i].trim();
    if (!line || line === "---") continue;
    
    // 1. Main Title: 🌐 TECH WORLD DAILY INTELLIGENCE
    if (line.indexOf("TECH WORLD DAILY INTELLIGENCE") !== -1 && (line.startsWith("#") || line.indexOf("🌐") !== -1)) {
      var cleanTitle = line.replace(/^[#\s]+/, "");
      var p = body.appendParagraph(cleanTitle);
      p.setHeading(DocumentApp.ParagraphHeading.HEADING1);
      p.setFontFamily(FONT_FAMILY);
      p.setFontSize(20);
      p.setBold(true);
      p.setForegroundColor(COLOR_PRIMARY);
      p.setSpacingBefore(0);
      p.setSpacingAfter(8);
      continue;
    }
    
    // 2. Section Headers: 🔥 TOP 5 DEVELOPMENTS, 🤖 AI RADAR, etc.
    if (line.match(/^#*\s*(🔥|🤖|👔|🚀|🧠|💻|☁️|🇮🇳|📈|💡)\s*[A-Z0-9\s&?()]+$/i) || 
        (line.startsWith("##") && !line.match(/^###/))) {
      var cleanSection = line.replace(/^[#\s]+/, "");
      var p = body.appendParagraph(cleanSection);
      p.setHeading(DocumentApp.ParagraphHeading.HEADING2);
      p.setFontFamily(FONT_FAMILY);
      p.setFontSize(14);
      p.setBold(true);
      p.setForegroundColor(COLOR_PRIMARY);
      p.setSpacingBefore(14);
      p.setSpacingAfter(6);
      continue;
    }
    
    // 3. Item Titles: 1. NVIDIA Backs... or ### 1. ...
    if (line.match(/^###?\s*\d+\.\s+/) || line.match(/^\d+\.\s+[A-Z0-9]/)) {
      var cleanItem = line.replace(/^[#\s]+/, "");
      var p = body.appendParagraph(cleanItem);
      p.setHeading(DocumentApp.ParagraphHeading.HEADING3);
      p.setFontFamily(FONT_FAMILY);
      p.setFontSize(11.5);
      p.setBold(true);
      p.setForegroundColor(COLOR_TEXT);
      p.setSpacingBefore(10);
      p.setSpacingAfter(4);
      continue;
    }
    
    // 4. Bullets: ● Importance: ... or * Importance: ... or ○ ...
    if (line.startsWith("●") || line.startsWith("*") || line.startsWith("-") || line.startsWith("○")) {
      var isSub = line.startsWith("○") || line.startsWith("  ");
      var cleanBullet = line.replace(/^[●\*\-○\s]+/, "");
      
      var p = body.appendParagraph((isSub ? "    ○ " : "  ● ") + cleanBullet);
      p.setFontFamily(FONT_FAMILY);
      p.setFontSize(10);
      p.setForegroundColor(COLOR_TEXT);
      p.setLineSpacing(1.15);
      p.setSpacingBefore(2);
      p.setSpacingAfter(2);
      
      formatInlineMarkdown(p, COLOR_LINK);
      continue;
    }
    
    // 5. Regular paragraphs (Date, Topic, Overall Tech Pulse, One Thing to Remember)
    var p = body.appendParagraph(line);
    p.setFontFamily(FONT_FAMILY);
    p.setFontSize(10);
    p.setForegroundColor(COLOR_TEXT);
    p.setLineSpacing(1.15);
    p.setSpacingBefore(2);
    p.setSpacingAfter(4);
    
    // Quote styling for One Thing to Remember
    if (line.startsWith('"') && line.endsWith('"')) {
      p.setBold(true);
      p.setFontSize(10.5);
      p.setForegroundColor(COLOR_PRIMARY);
      p.setSpacingBefore(6);
      p.setSpacingAfter(8);
    }
    
    formatInlineMarkdown(p, COLOR_LINK);
  }
}

// Helper to format **bold** and [links](url) inside a paragraph
function formatInlineMarkdown(paragraph, linkColor) {
  var text = paragraph.getText();
  
  // Format standard labels (Date:, Topic:, Overall Tech Pulse:, Importance:, etc.)
  var labels = ["Date:", "Topic:", "Overall Tech Pulse:", "Importance:", "Category:", "Verification Status:", 
                "What Happened:", "Why It Matters:", "What Changed:", "What's Next:", "Source:", 
                "Independent Coverage:", "Statement/Action:", "Classification:"];
  
  for (var k = 0; k < labels.length; k++) {
    var idx = text.indexOf(labels[k]);
    if (idx !== -1) {
      paragraph.editAsText().setBold(idx, idx + labels[k].length - 1, true);
    }
  }
  
  // Handle [Text](URL) markdown links
  var linkRegex = /\[([^\]]+)\]\((https?:\/\/[^\)]+)\)/g;
  var match;
  var currentText = text;
  
  while ((match = linkRegex.exec(currentText)) !== null) {
    var fullMatch = match[0];
    var linkTitle = match[1];
    var linkUrl = match[2];
    var startIdx = match.index;
    
    // Replace markdown link with plain title in text
    paragraph.replaceText(escapeRegex(fullMatch), linkTitle);
    currentText = paragraph.getText();
    
    // Set link URL and color
    var newStart = currentText.indexOf(linkTitle, startIdx);
    if (newStart !== -1) {
      var newEnd = newStart + linkTitle.length - 1;
      paragraph.editAsText().setLinkUrl(newStart, newEnd, linkUrl);
      paragraph.editAsText().setForegroundColor(newStart, newEnd, linkColor);
      paragraph.editAsText().setUnderline(newStart, newEnd, true);
    }
    linkRegex.lastIndex = startIdx + linkTitle.length;
  }
  
  // Clean remaining ** asterisks and bold content
  var boldRegex = /\*\*([^*]+)\*\*/g;
  var bMatch;
  var t = paragraph.getText();
  while ((bMatch = boldRegex.exec(t)) !== null) {
    var raw = bMatch[0];
    var inner = bMatch[1];
    var s = bMatch.index;
    paragraph.replaceText(escapeRegex(raw), inner);
    t = paragraph.getText();
    var ns = t.indexOf(inner, s);
    if (ns !== -1) {
      paragraph.editAsText().setBold(ns, ns + inner.length - 1, true);
    }
    boldRegex.lastIndex = s + inner.length;
  }
}

function escapeRegex(str) {
  return str.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
}
