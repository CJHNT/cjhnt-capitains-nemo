<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0" xmlns:t="http://www.tei-c.org/ns/1.0" exclude-result-prefixes="t">
    
    <xsl:strip-space elements="*" />
    <xsl:output omit-xml-declaration="yes" indent="yes"/>
        
    <!-- glyphs -->
    <xsl:template name="split-refs">
        <xsl:param name="pText"/>
        <xsl:if test="string-length($pText)">
            <xsl:if test="not($pText=.)">
                <xsl:text> </xsl:text>
            </xsl:if>
            <xsl:element name="a">
                <xsl:attribute name="href">
                    <xsl:value-of select="concat('http://cts.perseids.org/api/cts/?request=GetPassage', '&#38;', 'urn=', substring-before(concat($pText,','),','))"/>
                </xsl:attribute>
                <xsl:attribute name="target">_blank</xsl:attribute>
                <xsl:value-of select="substring-before(concat($pText,','),',')" />
            </xsl:element>
            <xsl:call-template name="split-refs">
                <xsl:with-param name="pText" select=
                    "substring-after($pText, ',')"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>

    <xsl:template match="//t:div[@type = 'translation']">
    <div>
      <xsl:attribute name="id">
        <xsl:text>translation</xsl:text>
        <xsl:if test="@xml:lang"><xsl:text>_</xsl:text></xsl:if>
        <xsl:value-of select="@xml:lang"/>
      </xsl:attribute>
      
      <xsl:attribute name="class">
        <xsl:text>translation lang_</xsl:text>
        <xsl:value-of select="@xml:lang"/>
      </xsl:attribute>
      
      
      <xsl:apply-templates/>
    
    </div>
  </xsl:template>
    
    <xsl:template match="t:w">
        <!-- I may need to add the ability to strip space from <p> tags if this produces too much space once we start exporting form CTE -->
        <!--<xsl:if test="not(preceding-sibling::node()[1][self::text()])">
            <xsl:text> </xsl:text>
        </xsl:if> -->       
        <xsl:element name="span">
            <xsl:attribute name="class">w<xsl:if test="current()[@lemmaRef]"><xsl:text> lexicon</xsl:text></xsl:if>
                <xsl:if test="parent::t:seg[@type='font-style:italic;']"><xsl:text> font-italic</xsl:text></xsl:if>
                <!-- The following will need to be changed to @type="platzhalter" once the files are reconverted -->
                <xsl:if test="parent::t:seg[@type='font-style:bold;']"><xsl:text> platzhalter</xsl:text></xsl:if>
                </xsl:attribute>
            <xsl:if test="@lemma">
                <xsl:attribute name="lemma"><xsl:value-of select="@lemma"/></xsl:attribute>
                <xsl:attribute name="onmouseover">showLemma(this)</xsl:attribute>
                <xsl:attribute name="onmouseout">hideLemma()</xsl:attribute>
            </xsl:if>
            <xsl:if test="@n">
                <xsl:attribute name="wordnum"><xsl:value-of select="@n"/></xsl:attribute>
            </xsl:if>
            <xsl:if test="parent::t:seg[@type='font-style:underline;']">
                <xsl:attribute name="data-lexicon"><xsl:value-of select="@lemmaRef"/></xsl:attribute>
                <xsl:attribute name="onclick">showLexEntry(this)</xsl:attribute>
            </xsl:if>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>
    
    <xsl:template match="t:pc">
        <xsl:element name="span">
            <xsl:attribute name="class">
                <xsl:text>pc_</xsl:text>
                <xsl:value-of select="@unit|@type"/>
            </xsl:attribute>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>

    <xsl:template match="//t:div[@type = 'commentary']">
    <div>
      <xsl:attribute name="id">
        <xsl:text>commentary</xsl:text>
        <xsl:if test="@xml:lang"><xsl:text>_</xsl:text></xsl:if>
        <xsl:value-of select="@xml:lang"/>
      </xsl:attribute>
      
      <xsl:attribute name="class">
        <xsl:text>commentary lang_</xsl:text>
        <xsl:value-of select="@xml:lang"/>
      </xsl:attribute>
      <xsl:attribute name="urn"><xsl:value-of select="@n"/></xsl:attribute>
      
      
      <xsl:apply-templates/>
    
    </div>
  </xsl:template>
    
    <xsl:template match="t:div[@type = 'edition']">
        <div id="edition">
            <xsl:attribute name="class">
                <xsl:text>edition lang_</xsl:text>
                <xsl:value-of select="@xml:lang"/>
            </xsl:attribute>
            <xsl:attribute name="data-lang"><xsl:value-of select="./@xml:lang"/></xsl:attribute>
            <xsl:if test="@xml:lang = 'heb'">
                <xsl:attribute name="dir">
                    <xsl:text>rtl</xsl:text>
                </xsl:attribute>
            </xsl:if>
            <xsl:attribute name="urn"><xsl:value-of select="@n"/></xsl:attribute>
            <xsl:apply-templates/>
        </div>
    </xsl:template>
    
    <xsl:template match="t:div[@type = 'textpart']">
        <xsl:element name="div">
            <xsl:attribute name="class">
                <xsl:value-of select="@subtype" />
            </xsl:attribute>
            <xsl:apply-templates select="@urn" />
            <xsl:if test="./@sameAs">
               <xsl:element name="p">
                   <xsl:element name="small">
                       <xsl:text>Sources </xsl:text>
                       <xsl:choose>
                           <xsl:when test="@cert = 'low'">
                               <xsl:text>(D'après)</xsl:text>
                           </xsl:when>
                       </xsl:choose>
                       <xsl:text> : </xsl:text>
                       <xsl:call-template name="split-refs">
                           <xsl:with-param name="pText" select="./@sameAs"/>
                       </xsl:call-template>
                   </xsl:element>
               </xsl:element>
            </xsl:if>
            <xsl:choose>
                <xsl:when test="child::t:l">
                    <ol><xsl:apply-templates /></ol>
                </xsl:when>
                <xsl:when test="not(descendant::t:div[@type='textpart'])">
                    <seg class="nt-cit"><xsl:for-each select="parent::t:div[@type='textpart']"><xsl:value-of select="@n"/><xsl:text>,</xsl:text></xsl:for-each><xsl:value-of select="@n"/>: </seg>
                    <xsl:apply-templates />
                </xsl:when>
                <xsl:otherwise>
                    <xsl:apply-templates/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:element>
    </xsl:template>
    
    <xsl:template match="t:l">
        <xsl:element name="li">
            <xsl:apply-templates select="@urn" />
            <xsl:attribute name="value"><xsl:value-of select="@n"/></xsl:attribute>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>
    
    <xsl:template match="t:lg">
        <xsl:element name="ol">
            <xsl:apply-templates select="@urn" />
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>
    
    <xsl:template match="t:pb">
        <div class='pb'><xsl:value-of select="@n"/></div>
    </xsl:template>
    
    <xsl:template match="t:ab/text()">
        <xsl:value-of select="." />
    </xsl:template>
    
    <xsl:template match="t:div[@subtype='verse']/t:p">
            <xsl:apply-templates select="@urn" />
            <xsl:apply-templates/>
    </xsl:template>
    
    <xsl:template match="t:lb" />
    
    <xsl:template match="t:ex">
        <span class="ex">
            <xsl:text>(</xsl:text><xsl:value-of select="." /><xsl:text>)</xsl:text>
        </span>
    </xsl:template>
    
    <xsl:template match="t:abbr">
        <span class="abbr">
            <xsl:text></xsl:text><xsl:value-of select="." /><xsl:text></xsl:text>
        </span>
    </xsl:template>  
    
    <xsl:template match="t:gap">
        <span class="gap">
            <xsl:choose>
                <xsl:when test="@quantity and @unit='character'">
                    <xsl:value-of select="string(@quantity)" />
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>---</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
            
        </span>
    </xsl:template>
    
    <xsl:template match="@urn">
        <xsl:attribute name="data-urn"><xsl:value-of select="."/></xsl:attribute>
    </xsl:template>
    
    <xsl:template match="t:sp">
        <section class="speak">
            <xsl:if test="./t:speaker">
                <em><xsl:value-of select="./t:speaker/text()" /></em>
            </xsl:if>
            <xsl:choose>
                <xsl:when test="./t:lg">
                    <xsl:apply-templates select="./t:lg" />
                </xsl:when>
                <xsl:when test="./t:p">
                    <xsl:apply-templates select="./t:p" />
                </xsl:when>
                <xsl:otherwise>
                    <ol>
                        <xsl:apply-templates select="./t:l"/>
                    </ol>
                </xsl:otherwise>
            </xsl:choose>
        </section>
    </xsl:template>
    
    <xsl:template match="t:supplied">
        <span>
            <xsl:attribute name="class">supplied supplied_<xsl:value-of select='@cert' /></xsl:attribute>
            <xsl:text>[</xsl:text>
            <xsl:apply-templates/><xsl:if test="@cert = 'low'"><xsl:text>?</xsl:text></xsl:if>
            <xsl:text>]</xsl:text>
        </span>
    </xsl:template>  
    
    <xsl:template match="t:note">
        <xsl:param name="note_num">
            <!-- I will need to change this to testing if there is an @n attribute. If so, use the value there. If not, find count(preceding::t:note[@type="a1"]) + 1 -->
            <xsl:choose>
                <xsl:when test="/t:TEI/t:text/t:body/t:div[1]/@xml:lang = 'deu'">
                    <xsl:number value="count(preceding::t:note) + 1" format="1"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:number value="count(preceding::t:note) + 1" format="a"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:param>
        <xsl:element name="sup">
            <xsl:element name="a">
                <xsl:attribute name="class">note</xsl:attribute>
                <xsl:attribute name="data-toggle">collapse</xsl:attribute>
                <xsl:attribute name="href"><xsl:value-of select="concat('#', generate-id())"/></xsl:attribute>
                <xsl:attribute name="role">button</xsl:attribute>
                <xsl:attribute name="aria-expanded">false</xsl:attribute>
                <xsl:attribute name="aria-controls"><xsl:value-of select="concat('multiCollapseExample', $note_num)"/></xsl:attribute>
                <xsl:attribute name="text-urn"><xsl:value-of select="translate(/t:TEI/t:text/t:body/t:div[1]/@n, ':.', '--')"/></xsl:attribute>
                <xsl:attribute name="type"><xsl:value-of select="@type"/></xsl:attribute>
                <xsl:value-of select="$note_num"/>
                <xsl:element name="span">
                    <xsl:attribute name="hidden">true</xsl:attribute>
                    <xsl:apply-templates mode="noteSegs"></xsl:apply-templates>
                </xsl:element>
            </xsl:element>
        </xsl:element>
    </xsl:template>
    
    <!-- I don't think there will be any more anchors in the next conversion, at least none without notes associated with them. So I think I can probably delete this template. -->
    <xsl:template match="t:anchor[ancestor-or-self::t:div[@xml:lang='lat']]">
        <xsl:param name="app_id" select="concat('#', translate(@xml:id, 'a', 'w'))"></xsl:param>
        <xsl:param name="note_num"><xsl:number value="count(preceding::t:anchor) + 1" format="a"/></xsl:param>
        <xsl:element name="sup">
            <xsl:element name="a">
                <xsl:attribute name="class">note</xsl:attribute>
                <xsl:attribute name="data-toggle">collapse</xsl:attribute>
                <xsl:attribute name="href"><xsl:value-of select="concat('#', generate-id())"/></xsl:attribute>
                <xsl:attribute name="role">button</xsl:attribute>
                <xsl:attribute name="aria-expanded">false</xsl:attribute>
                <xsl:attribute name="aria-controls"><xsl:value-of select="concat('multiCollapseExample', $note_num)"/></xsl:attribute>
                <xsl:value-of select="$note_num"/>
                <xsl:element name="span">
                    <xsl:attribute name="hidden">true</xsl:attribute>
                    <xsl:apply-templates mode="found" select="//t:app[@from=$app_id]"/>
                </xsl:element>
            </xsl:element>
        </xsl:element>
    </xsl:template>
    
    <xsl:template match="t:app" mode="found">
        <xsl:for-each select="t:rdg">
            <xsl:choose>
                <xsl:when test="@wit">
                    <xsl:choose>
                        <xsl:when test="@wit='#'">
                            <xsl:value-of select="."/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="translate(@wit, '#', '')"/>: <xsl:value-of select="."/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:when>
                <xsl:when test="@source">
                    <xsl:choose>
                        <xsl:when test="@source='#'">
                            <xsl:value-of select="."/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="translate(@source, '#', '')"/>: <xsl:value-of select="."/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:when>
            </xsl:choose>
        </xsl:for-each>
    </xsl:template>
    
    <xsl:template match="t:app"/>
    
    <xsl:template match="t:choice">
        <span class="choice">
            <xsl:attribute name="title">
                <xsl:value-of select="reg" />
            </xsl:attribute>
            <xsl:value-of select="orig" /><xsl:text> </xsl:text>
        </span>
    </xsl:template>
    
    <xsl:template match="t:unclear">
        <span class="unclear"><xsl:value-of select="." /></span>
    </xsl:template>
    
    <xsl:template match="t:seg[@type='font-style:italic;']" mode="noteSegs">
        <span class="font-italic"><xsl:apply-templates/></span>
    </xsl:template>
    
    <xsl:template match="t:seg[@type='lex-title']">
        <strong><xsl:apply-templates/></strong>
    </xsl:template>
    
    <xsl:template match="t:list">
        <ul class="list-unstyled">
            <xsl:apply-templates/>
        </ul>
    </xsl:template>
    
    <xsl:template match="t:item">
        <li>
            <xsl:apply-templates/>
        </li>
    </xsl:template>
    
    <xsl:template match="t:div[@type='beleg-gruppe']">
        <xsl:variable name="prev-styles" select="count(preceding::t:div[@type='beleg-gruppe'])"/>
        <p>
            <button class="btn btn-link witness-text-collapse" data-toggle="collapse" aria-expanded="false">
                <xsl:attribute name="data-target">#witness-text-collapse<xsl:value-of select="$prev-styles"/></xsl:attribute>
                <xsl:attribute name="aria-controls">witness-text-collapse<xsl:value-of select="$prev-styles"/></xsl:attribute>
<!--                <xsl:value-of select="t:head[@type='cjh-Überschrift-3']"/>-->
                <xsl:for-each select="t:head[@type='cjh-Überschrift-3']/node()">
                    <xsl:choose>
                        <xsl:when test="self::text()"><xsl:value-of select="."/></xsl:when>
                        <xsl:otherwise><xsl:apply-templates select="."></xsl:apply-templates></xsl:otherwise>
                    </xsl:choose>
                </xsl:for-each>
            </button>            
        </p>
        <div class="collapse">
            <xsl:attribute name="id">witness-text-collapse<xsl:value-of select="$prev-styles"/></xsl:attribute>
            <div class="card card-body">
                <xsl:apply-templates/>
            </div>
        </div>
    </xsl:template>
    
    <xsl:template match="t:ref[@type='erläuterungPointer']">
        <sup>
            <xsl:attribute name="target"><xsl:value-of select="@target"/></xsl:attribute>
            <xsl:apply-templates/>
        </sup>
    </xsl:template>
    
    <xsl:template match="t:note[@type='zitatErläuterung']">
        <seg>
            <xsl:attribute name="xml:id"><xsl:value-of select="@xml:id"/></xsl:attribute>
            <sup><xsl:value-of select="@n"/></sup>
            <xsl:apply-templates/>
        </seg>
    </xsl:template>
    
    <xsl:template match="t:seg[@type='belegstelle']">
        <button class="source-button btn btn-link" aria-expanded="false">
            <xsl:attribute name="target">
                <xsl:value-of select="@target"/>
            </xsl:attribute>
            <xsl:attribute name="urn">
                <xsl:value-of select="@cRef"/>
            </xsl:attribute>
            <xsl:attribute name="id">source-button<xsl:value-of select="count(preceding::t:seg[@type='belegstelle'])"/></xsl:attribute>
            <xsl:attribute name="data-target">#source-collapse<xsl:value-of select="count(preceding::t:div[@type='sectionB'])"/></xsl:attribute>
            <xsl:attribute name="aria-controls">source-collapse<xsl:value-of select="count(preceding::t:div[@type='sectionB'])"/></xsl:attribute>
            <xsl:value-of select="." />
        </button>
    </xsl:template>
    
    <xsl:template match="t:div[@type='sectionB']">
        <p>
            <xsl:apply-templates/>
            <xsl:element name="div">
                <xsl:attribute name="class">collapse source-collapse</xsl:attribute>
                <xsl:attribute name="id">source-collapse<xsl:value-of select="count(preceding::t:p[@n='quellen'])"/></xsl:attribute>
            </xsl:element>
        </p>
    </xsl:template>
    
    <xsl:template match="/t:TEI/t:text/t:body/t:div/t:div[@source]">
        <xsl:element name="p">
            <xsl:attribute name="class">nt-source-text</xsl:attribute>
            <xsl:attribute name="source-text"><xsl:value-of select="substring-before(@source, ';')"/></xsl:attribute>
            <xsl:attribute name="source-verse"><xsl:value-of select="substring-before(substring-after(@source, ';'), ';')"/></xsl:attribute>
            <xsl:attribute name="source-words"><xsl:value-of select="substring-after(substring-after(@source, ';'), ';')"/></xsl:attribute>
            Loading...
        </xsl:element>
        <xsl:apply-templates></xsl:apply-templates>
    </xsl:template>
    
    <xsl:template match="t:head">
        <xsl:element name="p">
            <xsl:attribute name="class"><xsl:value-of select="@type"/></xsl:attribute>
            <xsl:apply-templates />
            <xsl:apply-templates select="@urn" />
        </xsl:element>
    </xsl:template>
    
    <xsl:template match="t:p[not(@n='source-text')]">
        <p>
            <xsl:apply-templates select="@urn" />
            <xsl:apply-templates/>
        </p>
    </xsl:template>
    
    <xsl:template match="t:p[contains(@n, 'source-text')]"/>
    
    <xsl:template match="t:p[contains(@n, 'source-text')]" mode="show">
        <xsl:apply-templates select="@urn" />
        <xsl:apply-templates/>
    </xsl:template>
    
    <xsl:template match="t:div[@type='commentary']/t:div[@source]/t:div">
        <div><xsl:attribute name="type"><xsl:value-of select="@type"/></xsl:attribute><xsl:apply-templates/></div>
    </xsl:template>
    
    <xsl:template match="t:teiHeader"></xsl:template>
    
</xsl:stylesheet>

