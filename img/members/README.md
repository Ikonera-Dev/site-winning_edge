# img/members/ — member photos

Your own member photos go here. The site uses them in place of the BNI
Connect photo.

1. Save the photo here, named after the person: `adam-bortolussi.jpg`
   (lowercase, hyphens, `.jpg`, `.png` or `.webp`).
2. In `data/members.js`, set that person's `photo` field to the path:
   `"photo": "img/members/adam-bortolussi.jpg"`

Spec: square, at least 160×160 px (cards show it at 52–72 px, so this keeps
it sharp on retina screens), under ~100 KB.

To go back to the BNI Connect photo, set `"photo": ""`. `bniPhoto` is
refreshed from BNI on every sync, so edit `photo`, not that one.

Everything in this repo is public on the live site, so only add photos
the member is happy to have online.
