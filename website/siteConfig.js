/**
 * Copyright (c) 2017-present, Facebook, Inc.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 *
 * @format
 */

// See https://docusaurus.io/docs/site-config for all the possible
// site configuration options.

// Define this so it can be easily modified in scripts (to host elsewhere)
const baseUrl = "/";

// List of projects/orgs using your project for the users page.
const users = [];

const siteConfig = {
  title: "Captum",
  tagline: "Model Interpretability for PyTorch",
  url: "https://captum.ai",
  baseUrl: baseUrl,
  cleanUrl: true, // No .html extensions for paths

  // used for publishing and more
  organizationName: "pytorch",
  projectName: "captum",

  // Google analytics
  gaTrackingId: "UA-139570076-2",

  // links that will be used in the header navigation bar
  headerLinks: [
    { doc: "introduction", label: "Docs" },
    { href: `${baseUrl}tutorials/`, label: "Tutorials" },
    { href: `${baseUrl}api/`, label: "API Reference" },
    { href: "https://github.com/pytorch/captum", label: "GitHub" },
    { search: true } // position search box to the very right
  ],

  // add users to the website
  users,

  // search integration w/ algolia
  algolia: {
    apiKey: "207c27d819f967749142d8611de7cb19",
    indexName: "captum"
  },

  // images for header/footer and favicon
  headerIcon: "img/captum_logo.svg",
  // footerIcon: 'img/captum-icon.png',
  favicon: "img/captum.ico",

  // colors for website
  colors: {
    primaryColor: "#f29837", // orange
    secondaryColor: "#f0bc40" // yellow
  },

  highlight: {
    theme: "default"
  },

  // custom scripts that are placed in <head></head> of each page
  scripts: [
    // Github buttons
    "https://buttons.github.io/buttons.js",
    // Copy-to-clipboard button for code blocks
    `${baseUrl}js/code_block_buttons.js`,
    "https://cdnjs.cloudflare.com/ajax/libs/clipboard.js/2.0.0/clipboard.min.js",
    // Mathjax for rendering math content
    `${baseUrl}js/mathjax.js`,
    "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.5/latest.js?config=TeX-AMS_HTML"
  ],

  // CSS sources to load
  stylesheets: [`${baseUrl}css/code_block_buttons.css`],

  // enable on-page navigation for the current documentation page
  onPageNav: "separate",

  // enable scroll to top button a the bottom of the site
  scrollToTop: true,

  // if true, expand/collapse links & subcategories in sidebar
  docsSideNavCollapsible: false,

  // URL for editing docs
  editUrl: "https://github.com/pytorch/captum/edit/master/docs/",

  // Disable logo text so we can just show the logo
  disableHeaderTitle: true,

  // Open Graph and Twitter card images
  ogImage: "img/captum-icon.png",
  twitterImage: "img/captum.png",

  // show html docs generated by sphinx
  wrapPagesHTML: true
};

module.exports = siteConfig;
