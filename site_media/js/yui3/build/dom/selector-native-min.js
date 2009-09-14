YUI.add("selector-native",function(A){(function(G){G.namespace("Selector");var E="compareDocumentPosition",F="ownerDocument",D="yui-tmp-",C=0;var B={_reLead:/^\s*([>+~]|:self)/,_reUnSupported:/!./g,_foundCache:[],_supportsNative:function(){return((G.UA.ie>=8||G.UA.webkit>525)&&document.querySelectorAll);},useNative:true,_toArray:function(I){var J=I,K,H;if(!I.slice){try{J=Array.prototype.slice.call(I);}catch(L){J=[];for(K=0,H=I.length;K<H;++K){J[K]=I[K];}}}return J;},_clearFoundCache:function(){var K=B._foundCache,I,H;for(I=0,H=K.length;I<H;++I){try{delete K[I]._found;}catch(J){K[I].removeAttribute("_found");}}K=[];},_compare:("sourceIndex" in document.documentElement)?function(K,J){var I=K.sourceIndex,H=J.sourceIndex;if(I===H){return 0;}else{if(I>H){return 1;}}return -1;}:(document.documentElement[E]?function(I,H){if(I[E](H)&4){return -1;}else{return 1;}}:function(L,K){var J,H,I;if(L&&K){J=L[F].createRange();J.setStart(L,0);H=K[F].createRange();H.setStart(K,0);I=J.compareBoundaryPoints(Range.START_TO_END,H);}return I;}),_sort:function(H){if(H){H=B._toArray(H);if(H.sort){H.sort(B._compare);}}return H;},_deDupe:function(I){var J=[],H=B._foundCache,K,L;for(K=0,L;L=I[K++];){if(!L._found){J[J.length]=H[H.length]=L;L._found=true;}}B._clearFoundCache();return J;},_prepQuery:function(K,J){var I=J.split(","),L=[],N=true,O=(K&&K.nodeType===9),M,H;if(K){if(!O){K.id=K.id||G.guid();for(M=0,H=I.length;M<H;++M){J="#"+K.id+" "+I[M];L.push({root:K,selector:J});}}else{L.push({root:K,selector:J});}}return L;},_nativeQuery:function(H,O,P){if(B._reUnSupported.test(H)){return G.Selector.query(H,O,P);}var L=P?null:[],M=P?"querySelector":"querySelectorAll",Q,J,I,N;O=O||G.config.doc;if(H){J=B._prepQuery(O,H);L=[];for(I=0,N;N=J[I++];){try{Q=N.root[M](N.selector);if(M==="querySelectorAll"){Q=B._toArray(Q);}L=L.concat(Q);}catch(K){}}if(J.length>1){L=B._sort(B._deDupe(L));}L=(P)?(L[0]||null):L;}return L;},filter:function(I,H){var J=[],K,L;if(I&&H){for(K=0,L;(L=I[K++]);){if(G.Selector.test(L,H)){J[J.length]=L;}}}else{}return J;},test:function(N,I,J){var K=false,H=I.split(","),M,L,O;if(N&&N.tagName){J=J||N.ownerDocument;if(!N.id){N.id=D+C++;}for(L=0,O;O=H[L++];){O+="#"+N.id;M=G.Selector.query(O,J,true);K=(M===N);if(K){break;}}}return K;}};if(G.UA.ie&&G.UA.ie<=8){B._reUnSupported=/:(?:nth|not|root|only|checked|first|last|empty)/;}if(B._supportsNative()&&B.useNative){G.Selector.query=G.Selector.query||B._nativeQuery;}G.mix(G.Selector,B,true);})(A);},"@VERSION@",{requires:["dom-base"]});